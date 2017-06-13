from jsonbuilder import *
import PQTrading
import logging
from datamanipulator import *
import pdb
import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


def _series(instruments, suffix=None, prefix=RawManipulator.PREFIX):
    return ','.join([prefix + ':' + i + (suffix if suffix is not None else '') for i in instruments])


def _ggrandchild_strategByAsset(trading_sys, instruments, start, finish):
    """
    Build a JSON page under each instrument, containing a bar chart of the weights placed on 
    every sub trading system under each trading system on a particular day
    Hierarchy level: great-grandchild
    """
    pages, views = [], []
    row = 1
    for system in sorted(trading_sys):
        tags = buildTags("Weights", series=_series(instruments, prefix=StratManipulator.PREFIX, suffix=':' + system),
                         start_date=start, end_date=finish, market=system, axis=trading_sys[system])
        views.append(buildViews("stratHistogram", tags, row))
        row += 1
    longName = PQTrading.instrumentToLongName[instruments[0][:3]]
    page = buildPage("Strategy Weights", views=views,
                     tags={"header": "{} strategy weights".format(longName), "datepicker": True})
    pages.append(page)
    return pages


def _grandchild_instrument(sub_pages, sub_instruments):
    """
    Build a JSON page for each instrument showing several statistical charts on the instrument
    Hierarchy level: grandchild
    """
    market = sub_instruments[0][:3]

    # Build tags for four graphs
    price_tag = buildTags("price", series=_series(sub_instruments, suffix='.prices'), market='{} Price'.format(market))
    vol_tag = buildTags("volatility", series=_series(sub_instruments, suffix='PositionVol.volatility'), market=market)
    pos_tag = buildTags("position", series=_series(sub_instruments, suffix='FinalPos.position'), market=market)
    pnl_tag = buildTags("accumulated", series=_series(sub_instruments, suffix='FinalPL.netPL', prefix=AccumManipulator.PREFIX),
                        market="{} accumulated net PnL".format(market))

    # Use the tags to build four views
    views = [buildViews("price", price_tag, 1), buildViews("volatility", vol_tag, 1),
             buildViews("position", pos_tag, 2), buildViews("accumulated", pnl_tag, 2)]

    # Create the child page for the instrument, passing in strategy-level pages
    instrument_name = PQTrading.instrumentToLongName[sub_instruments[0][:3]]

    # If instrument name contains (), use the part within the brackets
    try:
        instrument_name = instrument_name[instrument_name.index("(") + 1:instrument_name.rindex(")")]
    except:
        pass
    grandchild_page = buildPage(instrument_name, views=views, nodes=sub_pages,
                                tags={"header": "{} basic graphs".format(instrument_name), "datepicker": False})
    return grandchild_page


def _child_sector(sub_pages, series):
    """
    Group all instrument pages by sector. Showing all instruments' positions on the home page
    Hierarchy level: child
    """
    sector_pages = []
    for sector in sorted(sub_pages.keys()):
        sector_tags = buildTags("position", series=_series(series[sector]), market=sector)
        sector_view = [buildViews("position", sector_tags, 1)]
        sector_page = buildPage(sector, views=sector_view, nodes=sub_pages[sector],
                                tags={"header": "{} Positions".format(sector), "datepicker": False})
        sector_pages.append(sector_page)

        logging.info("Built webpage for %s sector", sector)
    return sector_pages


def _child_strategy(trading_sys, all_markets, start, finish):
    """
    Build a JSON page for each trading system, showing a bar chart of weights on 
    each sub system across all assets on a particular day
    Hierarchy level: child
    """
    pages, views = [], []
    # start = '20170519'
    # finish = '20170522'
    for system in sorted(trading_sys):
        views = []
        row = 1
        for subsys in trading_sys[system]:
            tags = buildTags(datatype="Weight", series=_series(['all'], prefix=StratManipulator.PREFIX, suffix=':'+subsys),
                             start_date=start, end_date=finish, market=subsys,
                             axis=[PQTrading.instrumentToLongName[i[:3]] for i in groupBySector(all_markets)])
            views.append(buildViews("stratHistogram", tags, row))
            row += 1
        page = buildPage(system, views=views,
                         tags={"header": "{} strategy weights".format(system), "datepicker": True})
        pages.append(page)

        logging.info("Built webpage for %s", system)
    return pages


def _parent_homepage(all_markets):
    """
    Build home page with multiple graphs of portfolio-level data
    Hierarchy level: parent
    """
    # Build PnL graph
    home_view = []
    row = 1
    portf_tag = buildTags("price", series=_series(['Portfolio.netPL', 'Portfolio.grossPL'], prefix=AccumManipulator.PREFIX), market='Net P&L')
    home_view.append(buildViews("price", portf_tag, row))
    row += 1

    # Build correlation table
    correl_tag = buildTags("price", series=CorrelManipulator.PREFIX + ":all", market='All Markets', axis=all_markets)
    home_view.append(buildViews("correlation", correl_tag, row))
    row += 1

    # Build histogram graph
    histo_tag = buildTags("price", series=RawManipulator.PREFIX + ":Portfolio.netPL", market="Annual Net Portf")
    home_view.append(buildViews("histogram", histo_tag, row))

    home_page = buildPage("Root", views=home_view,
                          tags={"header": "Portfolio Monitor", "datepicker": False})
    logging.info("Built home page")
    return home_page


def build_pages(data_provider, start='20170522', end='20170522'):
    """
    Build JSONG pages for the entire website
    """
    # instrument_list = ['CCEC1','CCEC2']
    all_markets = data_provider.get_instruments()
    trading_sys = data_provider.get_trading_sys()
    i, sub_instruments, ex_spreads_markets = 0, [], []

    sub_pages, instr_by_sector = {}, {}

    while i < len(all_markets):
        instrument = all_markets[i]

        # Skip all instruments that are spreads
        if instrument.startswith("Spread"):
            i += 1
            continue

        ex_spreads_markets.append(instrument) # List of all out-right markets, i.e. excluding spreads
        sub_instruments.append(instrument) # List of instruments with same 1st 3 letters (e.g. CCEC1, CCEC2 etc..)

        # If the next instrument has the same short name as the current instrument, go straight to the next loop.
        if i + 1 < len(all_markets) and instrument[:3] == all_markets[i + 1][:3]:
            i += 1
            continue

        ggrandchild_pages = _ggrandchild_strategByAsset(trading_sys, sub_instruments, start, end)

        grandchild_page = _grandchild_instrument(ggrandchild_pages, sub_instruments)

        # Match sector to corresponding instrument-level position data (for plot on sector home page)
        sector = PQTrading.instrumentToSector[instrument[:3]]
        sector_name = PQTrading.sectorCodeToName[sector]
        instr_by_sector[sector_name] = instr_by_sector.get(sector_name, []) + \
                                       [i + 'FinalPos.position' for i in sub_instruments]

        # Add the instrument as a child page into the corresponding sector page (parent)
        sub_pages[sector_name] = sub_pages.get(sector_name, [])
        sub_pages[sector_name].append(grandchild_page)

        # Reset the initial settings
        i += 1
        sub_instruments = []

    sector_pages = _child_sector(sub_pages, instr_by_sector)
    pages = [buildPage("Instruments", nodes=sector_pages)]
    strategy_pages = _child_strategy(trading_sys, ex_spreads_markets, start, end)
    pages += [buildPage("Strategies", nodes=strategy_pages)]

    pages.insert(0, _parent_homepage(ex_spreads_markets))
    return pages
