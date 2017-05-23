from jsonbuilder import *
import PQTrading
import logging
import pdb

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


def _build_trading_sys(trading_sys, instruments):
    pages, views = [], []

    for sys in sorted(trading_sys.keys()):
        sub_systems = trading_sys[sys]
        row = 1
        for instrument in instruments:
            tags = buildTags("Expected Return", series=','.join([instrument + s + '.expRtn' for s in sub_systems]),
                             market='{} {}'.format(instrument, sys))
            views.append(buildViews("price", tags, row))
            row += 1
        page = buildPage(sys, views)
        pages.append(page)
        views = []
        logging.info("Building page for %s system, %s instruments", sys, instruments)

    return pages


def _build_instrument_page(sub_instruments, grandchild_pages):

    market = sub_instruments[0][:3]

    # Build tags for four graphs
    price_tag = buildTags("price", series=','.join([i +'.prices' for i in sub_instruments]), market=market)
    vol_tag = buildTags("volatility", series=','.join([i +'PositionVol.volatility' for i in sub_instruments]), market=market)
    pos_tag = buildTags("position", series=','.join([i +'FinalPos.position' for i in sub_instruments]), market=market)
    pnl_tag = buildTags("price", series=','.join([i +'FinalPL.netPL' for i in sub_instruments]), market="{} net PnL".format(market))

    # Use the tags to build four views
    views = [buildViews("price", price_tag, 1), buildViews("volatility", vol_tag, 1),
             buildViews("position", pos_tag, 2), buildViews("accumulated", pnl_tag, 2)]

    # Create the child page for the instrument, passing in strategy-level pages
    child_page = buildPage(PQTrading.instrumentToLongName[sub_instruments[0][:3]], views, nodes=grandchild_pages)
    logging.info("Building webpage for %s instrument", sub_instruments[0][:3])
    return child_page


def _build_sector_page(sub_pages, series):
    sector_pages = []
    for sector in sorted(sub_pages.keys()):
        sector_tags = buildTags("position", series=', '.join(series[sector]), market=sector)
        sector_view = [buildViews("position", sector_tags, 1)]
        sector_page = buildPage(sector, sector_view, nodes=sub_pages[sector])
        sector_pages.append(sector_page)

        logging.info("Building webpage for %s sector", sector)
    return sector_pages


def _build_home_page(all_markets):
    # Build home page with multiple graphs
    # Build PnL graph
    home_view = []
    row = 1
    portf_tag = buildTags("price", series='Portfolio.netPL, Portfolio.grossPL', market='Net P&L')
    home_view.append(buildViews("accumulated", portf_tag, row))
    row += 1

    # Build correlation table
    all_series = ', '.join([n + '.prices' for n in all_markets])
    correl_tag = buildTags("price", series=all_series, market='All Markets', axis=all_markets)
    home_view.append(buildViews("correlation", correl_tag, row))
    row += 1

    # Build histogram graph
    histo_tag = buildTags("price", series="Portfolio.netPL", market="Annual Net Portf")
    home_view.append(buildViews("histogram", histo_tag, row))

    home_page = buildPage("Root", home_view)
    return home_page


def build_pages(data_provider):
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

        grandchild_pages = _build_trading_sys(trading_sys, sub_instruments)

        child_page = _build_instrument_page(sub_instruments, grandchild_pages)

        # Match sector to corresponding instrument-level position data (for plot on sector home page)
        sector = PQTrading.instrumentToSector[instrument[:3]]
        sector_name = PQTrading.sectorCodeToName[sector]
        instr_by_sector[sector_name] = instr_by_sector.get(sector_name, []) + [i + 'FinalPos.position' for i in sub_instruments]

        # Add the instrument as a child page into the corresponding sector page (parent)
        sub_pages[sector_name] = sub_pages.get(sector_name, [])
        sub_pages[sector_name].append(child_page)

        # Reset the initial settings
        i += 1
        sub_instruments = []

    pages = _build_sector_page(sub_pages, instr_by_sector)
    pages.insert(0, _build_home_page(ex_spreads_markets))
    return pages
