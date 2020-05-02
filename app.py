from flask import Flask, render_template, request
from datetime import datetime
import pandas as pd
import json
import os
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
import nltk
import re
from collections import Counter
from stop_words import get_stop_words
import operator

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Result


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = {}
    if request.method == 'POST':
        try:
            url = request.form['url']
            r = requests.get(url)
            print(r.text)
        except:
            errors.append(
                "Unable to get URL. Please make sure it's valid and try again."
            )
        if r:
            raw = BeautifulSoup(r.text, 'html.parser').get_text()
            nltk.data.path.append('./nltk_data/')
            tokens = nltk.word_tokenize(raw)
            words = nltk.Text(tokens)
            non_punc = re.compile('.*[A-Za-z]*.')
            raw_words = [text for text in words if non_punc.match(text)]
            raw_words_count = Counter(raw_words)
            stop_words = get_stop_words('en')
            no_stop_words = [w for w in raw_words if w.lower() not in stop_words]
            no_stop_count = Counter(no_stop_words)
            results = sorted(
                no_stop_count.items(),
                key=operator.itemgetter(1),
                reverse=True
            )
            try:
                result = Result(
                    url=url,
                    result_all=raw_words_count,
                    result_no_stop_words=no_stop_count
                )
                db.session.add(result)
                db.session.commit()
            except:
                errors.append("Unable to add item to database.")
                return render_template('index.html', errors=errors, results=results)

    return render_template('index.html')


@app.route('/api/v1/data/timeline', methods=['GET'])
def return_cases_timeline():
    raw_df = pd.read_csv('static/data/complete.csv', index_col=[0], parse_dates=True)

    coronavirus_df = raw_df.drop(labels=['confirmed1', 'confirmed2', 'Latitude', 'Longitude'], axis=1)
    states = coronavirus_df['state'].unique()
    grouped_by_state = coronavirus_df.groupby('state')
    state_data = [
        {
            "state": state,
            "data": json.loads(grouped_by_state.get_group(state).drop('state', axis=1).to_json(orient='index'))}
        for state in states
    ]
    return json.dumps(state_data)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
    print(os.environ['APP_SETTINGS'])
