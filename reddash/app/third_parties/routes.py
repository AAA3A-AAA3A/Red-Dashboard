from reddash.app.app import app

from flask import abort, flash, jsonify, redirect, render_template, render_template_string, url_for, request, session
from flask_babel import _
from flask_login import current_user, login_required
from flask_login import login_url as make_login_url
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import Python3TracebackLexer, get_lexer_by_name

from ..base.routes import get_guild, get_third_parties
from ..utils import get_result  # , get_user_id
from . import blueprint

# <---------- Third Parties ---------->


@blueprint.route("/api/webhook", methods=("POST",))
async def webhook_route():
    if not request.is_json:
        # Reject any requests that aren't json for now.
        return jsonify(
            {"status": 0, "message": "Invalid formatting. This endpoint receives JSON only."}
        )
    payload = request.get_json()
    payload["origin"] = request.origin
    payload["headers"] = str(
        request.headers
    )  # Pass header data here incase there was something else the user needs for filtering.
    payload["user_agent"] = str(
        request.user_agent
    )  # User agent seems adequate enough for filtering.
    try:
        requeststr = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "DASHBOARDRPC_WEBHOOKS__WEBHOOK_RECEIVE",
            "params": [payload],
        }
        with app.lock:
            return await get_result(app, requeststr)
    except Exception as e:
        app.logger.error("Error sending webhook data.", exc_info=e)


@blueprint.route("/third_party/callback/<provider>")
@blueprint.route("/oauth/callback/<provider>")
@login_required
async def oauth_route(provider: str):
    args = request.args.copy()
    args["provider"] = provider
    args["url"] = request.url
    requeststr = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "DASHBOARDRPC_THIRDPARTIES__OAUTH_RECEIVE",
        "params": [current_user.id, args],
    }
    with app.lock:
        await get_result(app, requeststr)
    return render_template("pages/third_parties/oauth.html", provider=provider)


@blueprint.route("/third-parties/<third_party>")
@blueprint.route("/third-parties")
@login_required
async def third_parties(third_party: str = None):
    return_third_parties = await get_third_parties()

    return render_template(
        "pages/third_parties/third_parties.html",
        **return_third_parties,
        tab_name=None
        if third_party is None or third_party not in return_third_parties["third_parties"]
        else third_party,
    )


@blueprint.route(
    "/dashboard/<guild_id>/third-party/<name>/<page>",
    methods=(
        "GET",
        "HEAD",
        "OPTIONS",
        "POST",
        "PATCH",
        "DELETE",
    ),
)
@blueprint.route(
    "/dashboard/<guild_id>/third-party/<name>",
    methods=(
        "GET",
        "HEAD",
        "OPTIONS",
        "POST",
        "PATCH",
        "DELETE",
    ),
)
@blueprint.route(
    "/third-party/<name>/<page>",
    methods=(
        "GET",
        "HEAD",
        "OPTIONS",
        "POST",
        "PATCH",
        "DELETE",
    ),
)
@blueprint.route(
    "/third-party/<name>",
    methods=(
        "GET",
        "HEAD",
        "OPTIONS",
        "POST",
        "PATCH",
        "DELETE",
    ),
)
async def third_party(name: str, page: str = None, guild_id: str = None):
    third_parties = app.variables["third_parties"]
    name = name.strip()
    if name not in third_parties:
        name = next((key for key in third_parties if key.lower() == name.lower()), None)
        if name is None:
            return abort(
                404, description=_("Looks like that third party doesn't exist... Strange...")
            )
    if name in app.data["disabled_third_parties"]:
        return abort(403, description=_("This third party is disabled."))
    if page is not None:
        page = _page = page.lower()
    else:
        _page = "null"
    if _page not in third_parties[name]:
        # if _page != "null" and page.isdecimal() and "null" in third_parties[name]:
        #     guild_id, page, _page = page, None, "null"
        return abort(404, description=_("Looks like that page doesn't exist... Strange..."))
    if request.method not in third_parties[name][_page]["methods"]:
        return abort(405, description=_("Method not allowed."))

    context_ids = {}
    if "user_id" in third_parties[name][_page]["context_ids"]:
        if current_user.is_authenticated:
            context_ids[
                "user_id"
            ] = current_user.id  # int(get_user_id(app=app, req=request, ses=session))
        else:
            return redirect(make_login_url("login_blueprint.login", next_url=request.url))
    if third_parties[name][_page]["is_owner"] and not current_user.is_owner:
        return abort(403, description=_("You must be the owner of the bot to access this page."))
    if "guild_id" in third_parties[name][_page]["context_ids"]:
        try:
            context_ids["guild_id"] = int(guild_id)
        except (TypeError, ValueError):
            return redirect(make_login_url("base_blueprint.dashboard", next_url=url_for("third_parties_blueprint.third_party", name=name, page=page, guild_id="GUILD_ID", **request.args)))
        return_guild = await get_guild(context_ids["guild_id"])
        if return_guild["guild"]["status"] == 1:
            return return_guild["guild"]
    else:
        return_guild = {}

    kwargs = request.args.copy()
    for key in third_parties[name][_page]["context_ids"]:
        if key in ("user_id", "guild_id"):
            continue
        try:
            context_ids[key] = int(kwargs.pop(key))
        except KeyError:
            return render_template("errors/custom.html", error_title=f"Missing argument: `{key}`.")
        except ValueError:
            return render_template("errors/custom.html", error_title=f"Invalid argument: `{key}`.")
    for key in third_parties[name][_page]["required_kwargs"]:
        if key not in kwargs:
            return render_template("errors/custom.html", error_title=f"Missing argument: `{key}`.")

    kwargs["data"] = request.json if request.method not in ("GET", "HEAD") else {}
    kwargs["form"] = request.form.copy()
    
    try:
        requeststr = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "DASHBOARDRPC_THIRDPARTIES__DATA_RECEIVE",
            "params": [
                request.method,
                name,
                page,
                request.url,
                session["csrf_token"],
                context_ids,
                kwargs,
                app.extensions["babel"].locale_selector(),
            ],
        }
        with app.lock:
            result = await get_result(app, requeststr)

        if "data" in result:
            result = result["data"]
        if "notifications" in result:
            for notification in result["notifications"]:
                flash(notification["message"], category=notification["category"])
        if request.method not in ["HEAD", "GET"]:  # API request by JavaScript code or bot.
            return result
        if "web_content" in result:
            if result["web_content"].get("standalone", False):
                return render_template_string(
                    name=name, page=page, **return_guild, **result["web_content"]
                )
            return render_template(
                "pages/third_parties/third_party.html",
                name=name,
                page=page,
                **return_guild,
                fullscreen=result["web_content"].get("fullscreen", False),
                source_content=render_template_string(
                    result["web_content"].pop("source"),
                    **result["web_content"],
                ),
            )
        elif "error_code" in result:
            return abort(result["error_code"], description=result.get("error_message"))
        elif "error_title" in result:
            return render_template(
                "errors/custom.html",
                error_title=result["error_title"],
                error_message=result.get("error_message"),
            )
        elif "redirect" in result:
            return redirect(result["redirect"])
        return result
    except Exception as e:
        app.logger.error(
            f"Error in the page `{page or 'Main Page'}` of the third party `{name}`.", exc_info=e
        )
        return abort(500, description=_("An error occurred while processing your request."))


@app.template_filter("highlight")
def highlight_filter(code, language="python"):
    if language == "traceback":
        lexer = Python3TracebackLexer()
    else:
        lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)
