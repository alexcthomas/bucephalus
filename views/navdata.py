import logging

import views.datamanipulator as dm
from views.jsonbuilder import build_page, build_views, build_tags

import PQTrading

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


def _series(instruments, suffix=None, prefix=dm.RawManipulator.PREFIX):
    return ','.join([prefix + ':' + i + (suffix if suffix is not None else '') for i in instruments])


def ggrandchild_strategByAsset(trading_sys, instruments):
    """
    Build a JSON page under each instrument, containing a time series of net optimised weights
    placed on every sub trading system
    Hierarchy level: great-grandchild
    """
    views = []
    for i in instruments:
        for row, system in enumerate(sorted(trading_sys)):
            series = ','.join([dm.RawManipulator.PREFIX + ':' + i + 'Combiner.{}'.format(subsys) \
                                   for subsys in trading_sys[system]])

            tags = build_tags("Weights", series=series, market=system, axis=trading_sys[system])

            views.append(build_views("price", tags, row+1))

    longName = PQTrading.instrumentToLongName[instruments[0][:3]]

    page = build_page("Optimised Weights",
                      views=views,
                      tags={"datepicker": False},
                      title="{} Net Optimised Weights".format(longName))

    return page


def ggrandchild_expRtn(trading_sys, instruments):
    """
    Build a JSON page under each instrument, containing a time series of expected return
    under each sub trading system within S-Oscillator
    Hierarchy level: great-grandchild
    """
    views = []
    for row, subsys in enumerate(trading_sys['STS']):
        series = _series(instruments, suffix='{}.expRtn'.format(subsys))
        tags = build_tags("Returns", series=series, market="STS")
        views.append(build_views("price", tags, row+1))

    longName = PQTrading.instrumentToLongName[instruments[0][:3]]

    page = build_page("Expected Return",
                      views=views,
                      tags={"datepicker": False},
                      title="{} Expected Return".format(longName))

    return page


def grandchild_instrument(sub_pages, sub_instruments):
    """
    Build a JSON page for each instrument showing several statistical charts on the instrument
    Hierarchy level: grandchild
    """
    market = sub_instruments[0][:3]

    # Build tags for four graphs
    price_tag = build_tags("price",
                           series=_series(sub_instruments, suffix='.prices'),
                           market='{} Price'.format(market))

    vol_tag = build_tags("volatility",
                         series=_series(sub_instruments, suffix='PositionVol.volatility'),
                         market=market)

    pos_tag = build_tags("position",
                         series=_series(sub_instruments, suffix='FinalPos.position'),
                         market=market)

    pnl_tag = build_tags("accumulated",
                         series=_series(sub_instruments, suffix='FinalPL.netPL', prefix=dm.AccumManipulator.PREFIX),
                         market="{} accumulated net PnL".format(market))

    ret_tag = build_tags("price",
                         series=_series(sub_instruments, suffix='Combiner.expRtn'),
                         market='{} Expected Return'.format(market))

    # Use the tags to build the views
    views = [build_views("price", price_tag, 1),
             build_views("volatility", vol_tag, 1),
             build_views("position", pos_tag, 2),
             build_views("accumulated", pnl_tag, 2),
             build_views("price", ret_tag, 3)]

    # Create the child page for the instrument, passing in strategy-level pages
    instrument_name = PQTrading.instrumentToLongName[sub_instruments[0][:3]]

    # If instrument name contains (), use the part within the brackets
    try:
        instrument_name = instrument_name[instrument_name.index("(") + 1:instrument_name.rindex(")")]
    except:
        pass

    page = build_page(instrument_name,
                      views=views,
                      nodes=sub_pages,
                      tags={"datepicker": False},
                      title="{} Basic Graphs".format(instrument_name))
    return page


def child_sector(sub_pages, sector_dict):
    """
    Group all instrument pages by sector. Showing all instruments' positions on the home page
    Hierarchy level: child
    """
    pages = []
    prefix = dm.AccumManipulator.PREFIX

    for sector in sorted(sub_pages.keys()):

        sector_tags = build_tags("position",
                                 series=_series(sector_dict[sector], suffix='FinalPos.position'),
                                 market=sector)

        grosspnl_tags = build_tags("pnl",
                                   series=_series(sector_dict[sector], prefix=prefix, suffix='FinalPL.grossPL'),
                                   market=sector+" Gross PnL")

        netpnl_tags = build_tags("pnl",
                                 series=_series(sector_dict[sector], prefix=prefix, suffix='FinalPL.netPL'),
                                 market=sector+" Net PnL")

        sector_view = [build_views("position", sector_tags, 1),
                       build_views("price", grosspnl_tags, 2),
                       build_views("price", netpnl_tags, 3)]

        page = build_page(sector,
                          views=sector_view,
                          nodes=sub_pages[sector],
                          tags={"datepicker": False},
                          title="{} Basic Graphs".format(sector))

        pages.append(page)

        logging.info("Built webpage for %s sector", sector)
    return pages


def child_strategy(trading_sys, all_markets, start, finish):
    """
    Build a JSON page for each trading system, showing a bar chart of weights on
    each sub system across all assets on a particular day
    Hierarchy level: child
    """
    pages, views = [], []
    for system in sorted(trading_sys):
        views = []
        for row, subsys in enumerate(trading_sys[system]):
            tags = build_tags(datatype="Weight",
                              series=_series(['all'], prefix=dm.StratManipulator.PREFIX, suffix=':'+subsys),
                              start_date=start, end_date=finish, market=subsys,
                              axis=[PQTrading.instrumentToLongName[i[:3]] for i in dm.groupBySector(all_markets)])

            views.append(build_views("stratHistogram", tags, row+1))

        page = build_page(system,
                          views=views,
                          tags={"datepicker": True},
                          title="{} Strategy Weights".format(system))

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
    portf_tag = build_tags("price",
                           series=_series(['Portfolio.netPL', 'Portfolio.grossPL'], prefix=dm.AccumManipulator.PREFIX),
                           market='Net P&L')

    home_view.append(build_views("price", portf_tag, row))
    row += 1

    # Build correlation table
    correl_tag = build_tags("price",
                            series=dm.CorrelManipulator.PREFIX + ":all",
                            market='All Markets', axis=all_markets)

    home_view.append(build_views("correlation", correl_tag, row))
    row += 1

    # Build histogram graph
    histo_tag = build_tags("price",
                           series=dm.RawManipulator.PREFIX + ":Portfolio.netPL",
                           market="Annual Net Portf")

    home_view.append(build_views("histogram", histo_tag, row))

    page = build_page("Root",
                      views=home_view,
                      tags={"datepicker": False},
                      title="Portfolio Monitor")

    logging.info("Built home page")
    return page


def parent_risk(risk_factors):
    views = []
    for row, factor in enumerate(risk_factors):
        tags = build_tags(datatype="price",
                          series=dm.RawManipulator.PREFIX + ":EPV." + factor)

        views.append(build_views("price", tags, row+1))

    page = build_page("Risk",
                      views=views,
                      tags={"datepicker": False},
                      title="Risk Factors")

    return page


def parent_pnl(instr_to_sector):
    """
    Build PnL page where gross and net PnL were shown as a break down by sectors
    Hierarchy level: parent
    """
    views = []
    for row, i in enumerate(["grossPL", "netPL"]):

        series = _series([sector for sector in instr_to_sector.keys()],
                         prefix=dm.SectorManipulator.PREFIX,
                         suffix=".{}".format(i))

        tags = build_tags("PnL", series=series, market=i)

        views.append(build_views("price", tags, row+1))

    page = build_page("Sector PnL",
                      views=views,
                      tags={"datepicker": False},
                      title="PnL by Sector")

    return page


def parent_portfPnL(instr_to_sector, start, end):
    views = []
    series = _series(['all.grossPL', 'all.netPL'], prefix=dm.StackManipulator.PREFIX)

    tags = build_tags("PnL", series=series, start_date=start, end_date=end, market='PnL')

    views.append(build_views("stackcol", tags, 1))

    page = build_page("Portfolio PnL Breakdown",
                      views=views,
                      tags={"datepicker": "range"},
                      title="Portfolio PnL Breakdown")

    return page


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

        ggrandchild = [ggrandchild_strategByAsset(trading_sys, sub_instruments),
                       (ggrandchild_expRtn(trading_sys, sub_instruments))]

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
    strategy_pages = child_strategy(trading_sys, ex_spreads_markets, start, end)

    pages = [parent_homepage(ex_spreads_markets),
             build_page("Instruments", nodes=sector_pages),
             build_page("Strategies", nodes=strategy_pages),
             parent_risk(["alpha", "multiplier", "thermostat", "var"]),
             parent_pnl(instr_to_sector),
             parent_portfPnL(instr_to_sector, start, end)]

    return pages




