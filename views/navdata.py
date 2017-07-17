from jsonbuilder import *
import PQTrading
import logging
from datamanipulator import *
import math
import pdb
import datetime

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


def _series(instruments, suffix=None, prefix=RawManipulator.PREFIX):
    return ','.join([prefix + ':' + i + (suffix if suffix is not None else '') for i in instruments])


def ggrandchild_strategByAsset(trading_sys, instruments):
    """
    Build a JSON page under each instrument, containing a time series of net optimised weights
    placed on every sub trading system
    Hierarchy level: great-grandchild
    """
    views = []
    row = 1
    for i in instruments:
        for system in sorted(trading_sys):
            series = ','.join([RawManipulator.PREFIX + ':' + i + 'Combiner.{}'.format(subsys) for subsys in trading_sys[system]])
            tags = buildTags("Weights", series=series, market=system, axis=trading_sys[system])
            views.append(buildViews("price", tags, row))
            row += 1
        row = 1
    longName = PQTrading.instrumentToLongName[instruments[0][:3]]
    pages = [buildPage("Optimised Weights", views=views, tags={
        "header": "{} Net Optimised Weights".format(longName), "datepicker": False})]
    return pages


def ggrandchild_expRtn(trading_sys, instruments):
    """
    Build a JSON page under each instrument, containing a time series of expected return
    under each sub trading system within S-Oscillator
    Hierarchy level: great-grandchild
    """
    views = []
    row = 1
    for subsys in trading_sys['STS']:
        series = _series(instruments, suffix='{}.expRtn'.format(subsys))
        tags = buildTags("Returns", series=series, market="STS")
        views.append(buildViews("price", tags, row))
        row += 1
    longName = PQTrading.instrumentToLongName[instruments[0][:3]]
    pages = [buildPage("Expected Return", views=views, tags={
        "header": "{} Expected Return".format(longName), "datepicker": False})]
    return pages


def grandchild_instrument(sub_pages, sub_instruments):
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
    ret_tag = buildTags("price", series=_series(sub_instruments, suffix='Combiner.expRtn'),
                        market='{} Expected Return'.format(market))

    # Use the tags to build the views
    views = [buildViews("price", price_tag, 1), buildViews("volatility", vol_tag, 1),
             buildViews("position", pos_tag, 2), buildViews("accumulated", pnl_tag, 2),
             buildViews("price", ret_tag, 3)]

    # Create the child page for the instrument, passing in strategy-level pages
    instrument_name = PQTrading.instrumentToLongName[sub_instruments[0][:3]]

    # If instrument name contains (), use the part within the brackets
    try:
        instrument_name = instrument_name[instrument_name.index("(") + 1:instrument_name.rindex(")")]
    except:
        pass
    grandchild_page = buildPage(instrument_name, views=views, nodes=sub_pages,
                                tags={"header": "{} Basic Graphs".format(instrument_name), "datepicker": False})
    return grandchild_page


def child_sector(sub_pages, sector_dict):
    """
    Group all instrument pages by sector. Showing all instruments' positions on the home page
    Hierarchy level: child
    """
    sector_pages = []
    for sector in sorted(sub_pages.keys()):
        sector_tags = buildTags("position", series=_series(sector_dict[sector], suffix='FinalPos.position'), market=sector)
        grosspnl_tags = buildTags("pnl", series=_series(sector_dict[sector], prefix=AccumManipulator.PREFIX,
                                                        suffix='FinalPL.grossPL'), market=sector+" Gross PnL")
        netpnl_tags = buildTags("pnl", series=_series(sector_dict[sector], prefix=AccumManipulator.PREFIX,
                                                      suffix='FinalPL.netPL'), market=sector+" Net PnL")
        sector_view = [buildViews("position", sector_tags, 1), buildViews("price", grosspnl_tags, 2),
                       buildViews("price", netpnl_tags, 3)]
        sector_page = buildPage(sector, views=sector_view, nodes=sub_pages[sector],
                                tags={"header": "{} Basic Graphs".format(sector), "datepicker": False})
        sector_pages.append(sector_page)

        logging.info("Built webpage for %s sector", sector)
    return sector_pages


def child_strategy(trading_sys, all_markets, start, finish):
    """
    Build a JSON page for each trading system, showing a bar chart of weights on 
    each sub system across all assets on a particular day
    Hierarchy level: child
    """
    pages, views = [], []
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
                         tags={"header": "{} Strategy Weights".format(system), "datepicker": True})
        pages.append(page)

        logging.info("Built webpage for %s", system)
    return pages


def parent_homepage(all_markets):
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


def parent_risk(risk_factors):
    views = []
    row = 1
    for factor in risk_factors:
        tags = buildTags(datatype="price", series=RawManipulator.PREFIX + ":EPV." + factor)
        views.append(buildViews("price", tags, row))
        row += 1
    page = [buildPage("Risk", views=views, tags={"header": "Risk Factors", "datepicker": False})]
    return page


def parent_pnl(instr_to_sector):
    """
    Build PnL page where gross and net PnL were shown as a break down by sectors
    Hierarchy level: parent
    """
    views = []
    row = 1
    for i in ["grossPL", "netPL"]:
        series = _series([sector for sector in instr_to_sector.keys()], prefix=SectorManipulator.PREFIX,
                         suffix=".{}".format(i))
        tags = buildTags("PnL", series=series, market=i)
        views.append(buildViews("price", tags, row))
        row += 1
    pages = [buildPage("Sector PnL", views=views, tags={"header": "PnL by Sector", "datepicker": False})]
    return pages


def parent_portfPnL(instr_to_sector, start, end):
    views = []
    row = 1
    series = _series(['all.grossPL', 'all.netPL'], prefix=StackManipulator.PREFIX)
    tags = buildTags("PnL", series=series, start_date=start, end_date=end, market='PnL')
    views.append(buildViews("stackcol", tags, row))
    pages = [buildPage("Portfolio PnL Breakdown", views=views, tags={"header": "Portfolio PnL Breakdown", "datepicker": "range"})]
    return pages


def build_pages(data_provider, start='20170522', end='20170522'):
    """
    Build JSON pages for the entire website
    """
    all_markets = data_provider.get_instruments()
    trading_sys = data_provider.get_trading_sys()

    # all_markets = ['CCEC1','CCEC2']
    i, sub_instruments, ex_spreads_markets = 0, [], []

    sub_pages, instr_to_sector = {}, {}

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

        ggrandchild = ggrandchild_strategByAsset(trading_sys, sub_instruments) + (ggrandchild_expRtn(trading_sys, sub_instruments))
        grandchild = grandchild_instrument(ggrandchild, sub_instruments)

        # Match sector to corresponding instrument-level position data (for plot on sector home page)
        sector = PQTrading.instrumentToSector[instrument[:3]]
        sector_name = PQTrading.sectorCodeToName[sector]
        instr_to_sector[sector_name] = instr_to_sector.get(sector_name, []) + [i for i in sub_instruments]

        # Add the instrument as a child page into the corresponding sector page (parent)
        sub_pages[sector_name] = sub_pages.get(sector_name, [])
        sub_pages[sector_name].append(grandchild)

        # Reset the initial settings
        i += 1
        sub_instruments = []

    sector_pages = child_sector(sub_pages, instr_to_sector)
    pages = [buildPage("Instruments", nodes=sector_pages)]
    strategy_pages = child_strategy(trading_sys, ex_spreads_markets, start, end)
    pages += [buildPage("Strategies", nodes=strategy_pages)]
    pages += parent_risk(["alpha", "multiplier", "thermostat", "var"])
    pages += parent_pnl(instr_to_sector)
    pages += parent_portfPnL(instr_to_sector, start, end)

    pages.insert(0, parent_homepage(ex_spreads_markets))
    return pages
