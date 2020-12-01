import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///grocerio.db")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide Username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide Password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Logged in Successfully!")
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password", 403)

        username = request.form.get("username")
        pw_hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        confirm = generate_password_hash(request.form.get("confirmation"), method='pbkdf2:sha256', salt_length=8)


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        if len(rows) != 0:
            flash("Username already exists.", 403)
        else:
            if request.form.get("password") != request.form.get("confirmation"):
                flash("Passwords do not match", 403)
            else:
                db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=pw_hash)
                rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)
                session["user_id"] = rows[0]["id"]
                return redirect("/home")

    else:
        return render_template("register.html")

@app.route("/home")
@login_required
def home():
    return render_template("homepage.html")

@app.route("/fruit", methods=["GET", "POST"])
@login_required
def fruit():
    if request.method == "POST":
        p_id = request.form['p_id']
        number = request.form.get("quantity")
        if not request.form.get("quantity"):
            flash("Enter quantity before purchasing")
            return redirect("/fruit")

        rows1 = db.execute("SELECT * FROM products WHERE product_id = :id", id=p_id)
        rows = db.execute("SELECT * FROM products Where type ='fruit'")
        lenrows = int(len(rows))
        lenrow=len(rows1)

        total = int(number) * int(rows1[0]['cost'])
        db1 = []
        for r in range(lenrow):
            db1.append(list(rows1[r].values()))

        record = db.execute("SELECT * FROM cart WHERE cart_id = :cart_id AND product_id=:product_id", cart_id = session["user_id"], product_id=p_id)
        if not record:
            db.execute("INSERT INTO cart (cart_id, product, quantity, price, total, product_id) VALUES (:cart_id, :product, :quantity, :price, :total, :product_id)",
                    cart_id = session["user_id"], product=db1[0][1], quantity=number, price=db1[0][2], total=total, product_id=p_id)
        else:
            db.execute("UPDATE cart SET quantity = quantity + :number WHERE cart_id=:id AND product_id=:product_id",
                            number=number, id=session["user_id"], product_id=p_id)
            db.execute("UPDATE cart SET total = total + :total WHERE cart_id=:id AND product_id=:product_id",
                            total=total, id=session["user_id"], product_id=p_id)

        last_product = db.execute("SELECT * FROM cart WHERE cart_id = :cart_id",cart_id = session["user_id"])
        l = len(last_product)

        flash(f"{db1[0][1]}, Qty:{number} is added to your Cart!")
        return render_template("fruit.html", lenrows=lenrows, rows=rows)

    else:
        rows = db.execute("SELECT * FROM products Where type ='fruit'")
        lenrows = int(len(rows))
        return render_template("fruit.html", lenrows=lenrows, rows=rows)


@app.route("/vegetable", methods=["GET", "POST"])
@login_required
def vegetable():
    if request.method == "POST":
        p_id = request.form['p_id']
        number = request.form.get("quantity")
        if not request.form.get("quantity"):
            flash("Enter quantity before purchasing")
            return redirect("/vegetable")

        rows1 = db.execute("SELECT * FROM products WHERE product_id = :id", id=p_id)
        rows = db.execute("SELECT * FROM products Where type ='vegetable'")
        lenrows = int(len(rows))
        lenrow=len(rows1)

        total = int(number) * int(rows1[0]['cost'])
        db1 = []
        for r in range(lenrow):
            db1.append(list(rows1[r].values()))

        record = db.execute("SELECT * FROM cart WHERE cart_id = :cart_id AND product_id=:product_id", cart_id = session["user_id"], product_id=p_id)
        if not record:
            db.execute("INSERT INTO cart (cart_id, product, quantity, price, total, product_id) VALUES (:cart_id, :product, :quantity, :price, :total, :product_id)",
                    cart_id = session["user_id"], product=db1[0][1], quantity=number, price=db1[0][2], total=total, product_id=p_id)
        else:
            db.execute("UPDATE cart SET quantity = quantity + :number WHERE cart_id=:id AND product_id=:product_id",
                            number=number, id=session["user_id"], product_id=p_id)
            db.execute("UPDATE cart SET total = total + :total WHERE cart_id=:id AND product_id=:product_id",
                            total=total, id=session["user_id"], product_id=p_id)

        flash(f"{db1[0][1]}, Qty:{number} is added to your Cart!")
        return render_template("vegetable.html", lenrows=lenrows, rows=rows)

    else:
        rows = db.execute("SELECT * FROM products Where type ='vegetable'")
        lenrows = int(len(rows))
        return render_template("vegetable.html", lenrows=lenrows, rows=rows)


@app.route("/groceries", methods=["GET", "POST"])
@login_required
def groceries():
    if request.method == "POST":
        p_id = request.form['p_id']
        number = request.form.get("quantity")
        if not request.form.get("quantity"):
            flash("Enter quantity before purchasing")
            return redirect("/groceries")

        rows1 = db.execute("SELECT * FROM products WHERE product_id = :id", id=p_id)
        rows = db.execute("SELECT * FROM products Where type ='grocery'")
        lenrows = int(len(rows))
        lenrow=len(rows1)

        total = int(number) * int(rows1[0]['cost'])
        db1 = []
        for r in range(lenrow):
            db1.append(list(rows1[r].values()))

        record = db.execute("SELECT * FROM cart WHERE cart_id = :cart_id AND product_id=:product_id", cart_id = session["user_id"], product_id=p_id)
        if not record:
            db.execute("INSERT INTO cart (cart_id, product, quantity, price, total, product_id) VALUES (:cart_id, :product, :quantity, :price, :total, :product_id)",
                    cart_id = session["user_id"], product=db1[0][1], quantity=number, price=db1[0][2], total=total, product_id=p_id)
        else:
            db.execute("UPDATE cart SET quantity = quantity + :number WHERE cart_id=:id AND product_id=:product_id",
                            number=number, id=session["user_id"], product_id=p_id)
            db.execute("UPDATE cart SET total = total + :total WHERE cart_id=:id AND product_id=:product_id",
                            total=total, id=session["user_id"], product_id=p_id)

        flash(f"{db1[0][1]}, Qty:{number} is added to your Cart!")
        return render_template("groceries.html", lenrows=lenrows, rows=rows)

    else:
        rows = db.execute("SELECT * FROM products Where type ='grocery'")
        lenrows = int(len(rows))
        return render_template("groceries.html", lenrows=lenrows, rows=rows)



@app.route("/healthcare", methods=["GET", "POST"])
@login_required
def healthcare():
    if request.method == "POST":
        p_id = request.form['p_id']
        number = request.form.get("quantity")
        if not request.form.get("quantity"):
            flash("Enter quantity before purchasing")
            return redirect("/healthcare")

        rows1 = db.execute("SELECT * FROM products WHERE product_id = :id", id=p_id)
        rows = db.execute("SELECT * FROM products Where type ='health'")
        lenrows = int(len(rows))
        lenrow=len(rows1)

        total = int(number) * int(rows1[0]['cost'])
        db1 = []
        for r in range(lenrow):
            db1.append(list(rows1[r].values()))

        record = db.execute("SELECT * FROM cart WHERE cart_id = :cart_id AND product_id=:product_id", cart_id = session["user_id"], product_id=p_id)
        if not record:
            db.execute("INSERT INTO cart (cart_id, product, quantity, price, total, product_id) VALUES (:cart_id, :product, :quantity, :price, :total, :product_id)",
                    cart_id = session["user_id"], product=db1[0][1], quantity=number, price=db1[0][2], total=total, product_id=p_id)
        else:
            db.execute("UPDATE cart SET quantity = quantity + :number WHERE cart_id=:id AND product_id=:product_id",
                            number=number, id=session["user_id"], product_id=p_id)
            db.execute("UPDATE cart SET total = total + :total WHERE cart_id=:id AND product_id=:product_id",
                            total=total, id=session["user_id"], product_id=p_id)

        flash(f"{db1[0][1]}, Qty:{number} is added to your Cart!")
        return render_template("healthcare.html", lenrows=lenrows, rows=rows)

    else:
        rows = db.execute("SELECT * FROM products Where type ='health'")
        lenrows = int(len(rows))
        return render_template("healthcare.html", lenrows=lenrows, rows=rows)

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "GET":
        items = db.execute("SELECT * FROM cart WHERE cart_id =:cart_id AND quantity > 0", cart_id = session["user_id"])
        grandtotal = db.execute("SELECT SUM(total) FROM cart WHERE cart_id =:cart_id", cart_id = session["user_id"])
        lenrow=len(items)
        kart = []
        for r in range(lenrow):
            kart.append(list(items[r].values()))
        lenkart=len(grandtotal)
        kart_total = []
        for r in range(lenkart):
            kart_total.append(list(grandtotal[r].values()))
        return render_template("cart.html", lenrow=lenrow, kart=kart, kart_total=kart_total)
    else:
        p_id = request.form['p_id']

        rows1 = db.execute("SELECT * FROM products WHERE product_id = :id", id=p_id)
        total = int(rows1[0]['cost'])

        db.execute("UPDATE cart SET quantity = quantity - 1 WHERE cart_id=:id AND product_id=:product_id", id=session["user_id"], product_id=p_id)
        db.execute("UPDATE cart SET total = total - :total WHERE cart_id=:id AND product_id=:product_id",
                    total=total, id=session["user_id"], product_id=p_id)

        flash("Item has been removed from your Cart!")
        return redirect("/cart")

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "GET":
        items = db.execute("SELECT * FROM cart WHERE cart_id =:cart_id AND quantity > 0", cart_id = session["user_id"])
        grandtotal = db.execute("SELECT SUM(total) FROM cart WHERE cart_id =:cart_id", cart_id = session["user_id"])
        lenrow=len(items)
        kart = []
        for r in range(lenrow):
            kart.append(list(items[r].values()))
        lenkart=len(grandtotal)
        kart_total = []
        for r in range(lenkart):
            kart_total.append(list(grandtotal[r].values()))
        return render_template("checkout.html", lenrow=lenrow, kart=kart, kart_total=kart_total)
    else:
        if not request.form.get("firstName"):
            flash("Must provide First Name")
            return redirect("/checkout")
        if not request.form.get("lastName"):
            flash("Must provide Last Name")
            return redirect("/checkout")
        if not request.form.get("address"):
            flash("Must provide Address")
        return redirect("/thanks")

@app.route("/thanks")
@login_required
def thanks():
    db.execute("DELETE FROM cart WHERE cart_id = :id", id=[session["user_id"]])
    return render_template("thanks.html")

