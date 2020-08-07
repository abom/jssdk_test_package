import os
import sys

from bottle import Bottle, request, response

from jumpscale.loader import j
from jumpscale.core.base import DuplicateError


current_full_path = os.path.dirname(os.path.abspath(__file__))
package_path = current_full_path.rpartition("wallet_example")[0]
sys.path.append(package_path)

from wallets_example.bottle import CONVERSION_TABLE, Currency, wallets

app = Bottle()


BASE_URL = "/api"
WALLETS_BASE_URL = f"{BASE_URL}/wallets"


def serialize(func):
    """
    json-serialize the return value
    """
    def decorator(*args, **kwargs):
        return j.data.serializers.json.dumps(func(*args, **kwargs))
    return decorator


@serialize
def format_error(status, message):
    """
    format error
    """
    data = {"status": status, "message": message}
    response.status = status
    response.content_type = "application/json"
    return data


def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS, DELETE"
        response.headers[
            "Access-Control-Allow-Headers"
        ] = "Access-Control-Allow-Origin, Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"

        if request.method != "OPTIONS":
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors


@app.get(WALLETS_BASE_URL)
@serialize
@enable_cors
def get_all():
    data = []
    for name in wallets.list_all():
        data.append(wallets.get(name).to_dict())
    return data


@app.get(f"{WALLETS_BASE_URL}/<wallet_id>")
@serialize
@enable_cors
def get(wallet_id):
    wallet = wallets.find(wallet_id)
    if not wallet:
        return format_error(404, f"wallet of {wallet_id} cannot be found")
    return wallet.to_dict()


@app.route(WALLETS_BASE_URL, method="options")
@enable_cors
def options_for_create():
    pass


@app.route(f"{WALLETS_BASE_URL}/<wallet_id>", method="options")
@enable_cors
def options_for_delete():
    pass


@app.route(f"{BASE_URL}/transfer", method="options")
@enable_cors
def options_for_transfer():
    pass

@app.post(WALLETS_BASE_URL)
@serialize
@enable_cors
def create():
    data = request.json
    if "id" not in data:
        return format_error(400, f"id is not specified")

    currency = data.get("currency")
    tags = data.get("tags", [])

    name = data["id"]

    try:
        wallet = wallets.new(name)
    except DuplicateError:
        return format_error(400, f"a wallet with the same of '{name}' already exists")
    except ValueError:
        return format_error(400, "name should only contain alphanumeric characters and should not start with a number")

    wallet.id = name
    wallet.address = j.data.hash.md5(name)
    wallet.balance = 0.0
    wallet.tags = tags
    if currency:
        wallet.currency = currency
    wallet.save()

    return wallet.to_dict()


@app.delete(f"{WALLETS_BASE_URL}/<wallet_id>")
@enable_cors
def delete(wallet_id):
    if wallet_id == "main":
        return format_error(400, f"cannot delete the main wallet")

    try:
        wallets.delete(wallet_id)
    except:
        pass


@app.get(f"{BASE_URL}/currency")
@serialize
@enable_cors
def get_currencies():
    return CONVERSION_TABLE


def get_by_address(address):
    _, count, result = wallets.find_many(address=address)
    if count:
        return next(result)


@app.post(f"{BASE_URL}/transfer")
@enable_cors
def transfer():
    data = request.json

    sender = data["sender"]
    receiver = data["receiver"]
    amount = data["amount"]

    sender_wallet = get_by_address(sender)
    if not sender_wallet:
        return format_error(404, f"sender wallet of {sender} cannot be found")

    receiver_wallet = get_by_address(receiver)
    if not receiver_wallet:
        return format_error(404, f"receiver wallet of {receiver} cannot be found")

    rate = CONVERSION_TABLE[sender_wallet.currency.value][receiver_wallet.currency.value]
    amount = amount * rate
    if sender_wallet.balance < amount:
        return format_error(400, f"insufficient funds")

    sender_wallet.balance -= amount
    receiver_wallet.balance += amount
    sender_wallet.save()
    receiver_wallet.save()


@app.get("/api/doc")
def api_doc():
    path = j.sals.fs.join_paths(j.sals.fs.parent(__file__), "apidoc.html")
    return j.tools.jinja2.get_template(path).render()
