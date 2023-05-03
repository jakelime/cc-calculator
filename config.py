
cfg={}

cfg['category_to_keys']={
        'BUS/MRT': '2', # BUS/MRT might or might not be qualified
        'SERAYA': '0',
        'GRAB': '0', # Grab wallet top up are not qualified
        'NUHMC-PHARMACY': '0',
        'NUH': '0', # Medical bills are not qualified
        'GIRO': '0',
        'CR': '0',
        'Previous': '0',
        'AXS': '0', # AXS transactions are not qualified
        'ATOME': '0', # ATOME is installment
        "APPLE.COM/BILL": "3",
        "CIRCLES.LIFE": "4",
        "UOB ONE CASH REBATE": "0",
        "ONE CARD ADDITIONAL REBATE": "0",
        }

cfg['keys_to_qualification']={
    ## True are qualified categories
    "0": False,
    "1": True,
    "2": False,
    "3": True,
    "4": True,
}


cfg['display_columns']=[
    "date_transacted",
    "posting_status",
    "key_code",
    "tier1_qualified",
    "short_description",
    "amount_sgd",
]
