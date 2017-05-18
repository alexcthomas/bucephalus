from jsonbuilder import *
import PQTrading
import pdb


def _build_instrument_page(data_provider):
    # Build a page of price charts and vol charts for each instrument
    price_names, vol_names = data_provider.get_instruments()
    # price_names, vol_names = ['CCEC1','CCEC2'], ['CCEC1PositionVol','CCEC2PositionVol']
    i, price_series, vol_series, pos_series, pnl_series = 0, [], [], [], []
    all_pages, all_markets = [], []
    while i < len(price_names):
        item = price_names[i]

        # Skip all instruments that are spreads
        if item.startswith("Spread"):
            i += 1
            continue

        # Add the instrument price in the all market list and series list.
        # Then check if the next instrument has the same short name as the current instrument.
        # If so, go straight to the next loop. Otherwise, loop through volatility database
        # to get all vol data under the same instrument (e.g. vol for CCEC1, CCEC2 etc..),
        # and build json view for the prices and volatility of this instrument
        all_markets.append(item)
        price_series.append(item + '.prices')
        pos_series.append(item + 'FinalPos.position')
        pnl_series.append(item + 'FinalPL.netPL')

        if i+1 < len(price_names) and item[:3] == price_names[i+1][:3]:
            i += 1
            continue

        price_tag = buildTags("price", series=','.join(price_series), market=item[:3])
        pos_tag = buildTags("position", series=','.join(pos_series), market=item[:3])
        pnl_tag = buildTags("price", series=','.join(pnl_series), market="{} net PnL".format(item[:3]))
        views = [buildViews("price", price_tag, 1)]

        for vol_item in vol_names:
            if vol_item.startswith("Spread"):
                continue
            elif vol_item.startswith(item[:3]):
                vol_series.append(vol_item+'.volatility')

        vol_tag = buildTags("volatility", series=','.join(vol_series), market=item[:3])
        views.append(buildViews("volatility", vol_tag, 1))

        views.append(buildViews("position", pos_tag, 2))
        views.append(buildViews("accumulated", pnl_tag, 2))

        # Build the page in json
        page = buildPage(PQTrading.instrumentToLongName[item[:3]], views)
        i += 1
        price_series, vol_series, pos_series, pnl_series = [], [], [], []
        all_pages.append(page)
    return all_pages, all_markets


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
    pages, markets = _build_instrument_page(data_provider)
    pages.append(_build_home_page(markets))
    # pdb.set_trace()
    return pages
