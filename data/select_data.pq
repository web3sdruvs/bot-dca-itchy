let
    url = "",
    source = Web.Contents(url),
    csvTable = Csv.Document(source, [Delimiter=","]),
    promoteHeader = Table.PromoteHeaders(csvTable, [PromoteAllScalars=true]),
    replace = Table.ReplaceValue(promoteHeader,".",",",Replacer.ReplaceText,{"quantity", "price", "dominance_btc_global", "percent_1h_token", "percent_24h_token", "percent_7d_token", "rsi_value", "intensity"}),
    change_type = Table.TransformColumnTypes(replace,{{"symbol", type text}, {"quantity", type number}, {"price", type number}, {"timestamp", type datetime}, {"index_current", Int64.Type}, {"index_class", type text}, {"dominance_btc_global", type number}, {"percent_1h_token", type number}, {"percent_24h_token", type number}, {"percent_7d_token", type number}, {"rsi_value", type number}, {"intensity", type number}})
in
    #"change_type"