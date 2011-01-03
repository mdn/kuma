from django.db import transaction

import cronjobs

from dashboards.models import PERIODS, WikiDocumentVisits


@cronjobs.register
def reload_wiki_traffic_stats():
    transaction.enter_transaction_management()
    transaction.managed(True)

    for period, _ in PERIODS:
        try:
            WikiDocumentVisits.reload_period_from_json(
                     period, WikiDocumentVisits.json_for(period))
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

    # Nice but not necessary when the process is about to exit:
    transaction.leave_transaction_management()
