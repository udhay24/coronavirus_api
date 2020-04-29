from flask import Flask
from datetime import datetime
import pandas as pd
import json
import os

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

@app.route('/')
def homepage():
    the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")

    return """
    <h1>Hello heroku</h1>
    <p>It is currently {time}.</p>
    <img src="http://loremflickr.com/600/400" />
    """.format(time=the_time)


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

