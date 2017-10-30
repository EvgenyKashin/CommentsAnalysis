from flask import Flask
from flask import render_template, jsonify
import json
from scripts import fit_predict
from flask import request
import os

app = Flask(__name__)
best_data = fit_predict.load_best_data()
fit_predict.load_model()

def make_table(coms, labels):
	template = """
	  <thead>
	    <tr>
	      <th>№</th>
	      <td>Комментарий</td>
	    </tr>
	  </thead>

	  <tbody>
	    {}
	  </tbody>
	"""

	template_row = """
	    <tr class="{}">
	      <th>{}</th>
	      <td>{}</td>
	    </tr>
	"""

	rows_text = ""
	for i, (c, l) in enumerate(zip(coms, labels)):
		class_value = 'success' if l else 'danger'
		rows_text += template_row.format(class_value, i, c)
	return template.format(rows_text)


@app.route('/')
def main():
	return render_template('index.html')

@app.route('/comments', methods=['GET'])
def comments(n=100):
	return jsonify(best_data.sample(n).text.tolist())

@app.route('/predict', methods=['POST'])
def predict():
	data = request.get_json()
	if len(data) < 5:
		return "";

	score, preds = fit_predict.predict_comments(data, with_separate=True)
	prediction_string = ""
	preds_table = make_table(data, preds)

	if score == 0:
		prediction_string = "Вы технарь!"
	elif score == 1:
		prediction_string = "Вы гумманитарий!"
	else:
		prediction_string = "Не возможно понять, попробуйте добавить еще один комментарий!"

	return jsonify([prediction_string, preds_table])

if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port, debug=False)