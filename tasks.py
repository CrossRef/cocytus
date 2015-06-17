from celery import Celery
import logging
import compare_change
from crossref_push import push_to_crossref

celery_service =  Celery('cocytus-tasks', broker='redis://localhost')

@celery_service.task
def process_change(change):
  """
  Recieve a diff from the RCStream, extract citation.
  """
  changes = compare_change.get_changes(change) 
  
  if 'doi' in changes and isinstance(changes['doi'], dict) and (changes['doi']['added'] or changes['doi']['deleted']): # one is not empty
    logging.info(u'change detected: ' + str(changes))
    process_output.delay(changes)
  elif type(changes) == dict and changes["type"] == "heartbeat":
    logging.info("pushing heartbeat")
    process_output.delay(changes)

@celery_service.task
def process_output(change):
  """
  Recieve a DOI citation, push it to a downstream celery_service.
  """
  logging.debug("Sending to CrossRef: " + str(change))
  response = push_to_crossref(change)
  logging.debug("CrossRef push response: " + str(response))
