from flask import Flask
from flask import render_template, jsonify
import json
from scripts import fit_predict
from flask import request

app = Flask(__name__)
best_data = fit_predict.load_best_data()
fit_predict.load_model()

@app.route('/')
def main():
	return render_template('index.html')

@app.route('/comments', methods=['GET'])
def comments(n=100):
	return jsonify(best_data.sample(n).text.tolist())

@app.route('/predict', methods=['POST'])
def predict():
	data = request.get_json();
	if len(data) < 5:
		return "";

	score = fit_predict.predict_comments(data);
	prediction_string = "";

	if score == 0:
		prediction_string = "Вы технарь!";
	elif score == 1:
		prediction_string = "Вы гумманитарий!";
	else:
		prediction_string = "Не возможно понять, попробуйте добавить еще один комментарий!";

	return prediction_string;

if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port, debug=False)