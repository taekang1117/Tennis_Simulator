from flask import Flask, render_template, request
from predictor import predict_match, load_all_stats_from_csv

app = Flask(__name__)
stat_dict = load_all_stats_from_csv()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        p1 = request.form["player1"].strip().replace(" ", "").lower()
        p2 = request.form["player2"].strip().replace(" ", "").lower()
        result = predict_match(p1, p2, stat_dict)
        return render_template("result.html", **result)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

