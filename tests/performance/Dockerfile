FROM hakobera/locust

RUN mkdir /tests
ADD ./smoke.py /tests/smoke.py
ENV SCENARIO_FILE /tests/smoke.py
