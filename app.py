from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from math import ceil

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

total_sales = 0.00

class Stocks(db.Model):
    name = db.Column(db.String(8), primary_key=True)
    amount = db.Column(db.Integer)

#最初のリクエストのときだけ実行してくれるデコレータ
@app.before_first_request
def init():
    db.create_all()

@app.route('/', methods=['GET'])
def hello():
    return "HELLO"

#認証されたときにアクセス．
#認証はapache側の設定で実装．
@app.route('/secret', methods=['GET'])
def success(): 
    return "SUCCESS"

@app.route('/management/stocks', methods=['GET', 'POST','DELETE'])
def stocks():
    global total_sales
    if request.method == 'POST':
        json = request.get_json()
        #入力が自然数かどうかの判定
        if (json["amount"]>0) & (isinstance(json["amount"],int)):
            #新規登録か更新かの判定
            #CREATE
            if Stocks.query.filter_by(name=json["name"]).scalar() is None:
                name = json["name"]

                #個数の指定があるかどうかの判定。なかったら一個として扱う。
                if "amount" in json:
                    amount = json["amount"]
                else:
                    amount = 1
                    
                stocks = Stocks(name=name, amount=amount)

                db.session.add(stocks)
                db.session.commit()
            #UPDATE
            else:
                stock = Stocks.query.get(json["name"])

                if "amount" in json:
                    amount = json["amount"]
                else:
                    amount = 1

                stock.amount += amount

                db.session.commit()

            return jsonify(json)
        else:
            return jsonify({"message": "ERROR"})
    #READ
    if request.method == 'GET':
        stocks = Stocks.query.order_by(Stocks.name).all()
        stocks_dict = {}
        for stock in stocks:
            if stock.amount != 0:
                stocks_dict[stock.name] = stock.amount

        return jsonify(stocks_dict)
    #DELETE
    else:
        delete_stocks = Stocks.query.all()
        for stock in delete_stocks:
            db.session.delete(stock)
        db.session.commit()

        total_sales = 0.00

        return jsonify({"message": "Deleted!"})

@app.route('/management/stocks/<name>', methods=['GET'])
def specified(name):
    #存在しない場合はエラー
    if Stocks.query.filter_by(name=name).scalar() is None:
        return jsonify({"message": "ERROR"})
    #READ
    else:
        stock = Stocks.query.get(name)
        stock_dict = {}
        stock_dict[stock.name] = stock.amount
        return jsonify(stock_dict)

@app.route('/management/sales', methods=['GET', 'POST'])
def sales():
    global total_sales
    if request.method == 'POST':
        json = request.get_json()

        #存在しなかったらエラー
        if Stocks.query.filter_by(name=json["name"]).scalar() is None:
            return jsonify({"message": "ERROR"})

        stock = Stocks.query.get(json["name"])
        #amountが省略されていないか
        if "amount" in json:
            #販売数が自然数かの判定
            if (json["amount"]>0) & (isinstance(json["amount"],int)):
                amount = json["amount"]
                
                #販売数が在庫を超えるなら、エラー
                if amount > stock.amount:
                    return jsonify({"message": "ERROR"})

                #価格の設定があるかの判定。なかったら個数だけ減る（タダで売る）。
                if "price" in json:
                    if json["price"] > 0:
                        total_sales += amount * json["price"]
                    #負の価格はエラー
                    else:
                        return jsonify({"message": "ERROR"})

                stock.amount -= amount

                #売った商品数を引いてUPDATE処理
                db.session.commit()

                return jsonify(json)
            else:
                return jsonify({"message": "ERROR"})
        #個数の指定がなかったら一個として扱う
        else:
            amount = 1
            #販売数が在庫を超えるなら、エラー
            if amount > stock.amount:
                return jsonify({"message": "ERROR"})

            if "price" in json:
                if json["price"] > 0:
                    total_sales += amount * json["price"]
                else:
                    return jsonify({"message": "ERROR"})
                    
            stock.amount -= amount

            #売った商品数を引いてUPDATE処理
            db.session.commit()

            return jsonify(json)
    #GETのときの処理
    else:
        #少数３桁以降切り上げ
        total_sales = ceil(100 * total_sales)/100
        sales_dict = {"sales": total_sales}
        return jsonify(sales_dict)

if __name__ == '__main__':
    app.run()