functions list:
    
    maturities(dt.datetime()) --> [float(front_wgt), float(back_wgt)]
    
    optionslam_scrape(str[ticker]) --> dict[earnings]
    
    yahoo_table_parse(str[raw_html_table]) --> DataFrame[ticker]
    
    yahoo_earnings(dt.datetime()) --> DataFrame[earnings_on_date]
    
    fundamentals(str[ticker]) --> DataFrame[stock_fundamentals]
    
    get_fundas(list[ticker_lst]) --> DataFrame[stock_fundamentals]
    
    historical_data(str[ticker], int[day_number], int[rolling_window], outsize[str]) --> DataFrame[daily_stock_data]
    
    current_volatility(list[ticker_lst], int[roll]) --> DataFrame[stock_volatilities]
    
    all_options(str[ticker], bool[greeks]) --> DataFrame[options_chains]
    
    earnings_condor(str[ticker], int[max_gap], int[dte_thresh], float[|money_thresh| <= 1]) -- DataFrame[condors], DataFrame[puts], DataFrame[calls]
    
    write_excel(str[filename], list[str[sheetnames]], list[dataframes]) --> void()