"""
Available endpoints:

- GET /wallets_example/api/ : list all wallets
- GET /wallets_example/api/<wallet id> : get wallet
- POST /wallets_example/api/ : create wallet
- DELETE /wallets_example/api/<wallet id> : delete wallet
- get /wallets_example/api/currency : get current available currencies and conversion rates
- POST /wallets_example/api/transfer : do a transfer
"""

from enum import Enum
from jumpscale.core.base import Base, fields, StoredFactory

class Currency(Enum):
    FTY = "fty"
    XDT = "xdt"
    CDT = "cdt"


CONVERSION_TABLE = {
    Currency.FTY.value: {
        Currency.FTY.value: 1,
        Currency.XDT.value: 2.5,
        Currency.CDT.value: 0.2
    },
    Currency.XDT.value: {
        Currency.FTY.value: 0.4,
        Currency.XDT.value: 1,
        Currency.CDT.value: 1,
    },
    Currency.CDT.value: {
        Currency.FTY.value: 5,
        Currency.XDT.value: 1,
        Currency.CDT.value: 1
    }
}


class Wallet(Base):
    id = fields.String()
    address = fields.String()
    balance = fields.Float()
    currency = fields.Enum(Currency)
    tags = fields.List(fields.String)


wallets = StoredFactory(Wallet)
wallets.always_reload = True
main_wallet = wallets.get("main")
main_wallet.id = "main"
main_wallet.address = "fad58de7366495db4650cfefac2fcd61"
main_wallet.currency = "fty"
if main_wallet.balance <= 0:
    # just give it 10000 again if it's 0
    main_wallet.balance = 100000
main_wallet.save()
