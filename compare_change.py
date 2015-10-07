import pywikibot
from bs4 import BeautifulSoup
import mwparserfromhell
import json
import ast
import time
import logging
import mwcites.extractors.doi

def wikitext_of_interest(wikitext):
    return set(ident.id for ident in mwcites.extractors.doi.extract(wikitext))
    
def single_comparator(page):
    comparands = {'deleted': [] , 'added': []}
    
    try:
        wikitext = page.get()
    except pywikibot.exceptions.IsRedirectPage:
        redir_target =  page.getRedirectTarget()
        # only trying one layer of redirect
        try:
            wikitext = redir_target.get()
            comparands['redirect'] = redir_target.title()
        except:
            return None

    except pywikibot.exceptions.NoPage:
        return None

    interests = wikitext_of_interest(wikitext)
    comparands['added'] = list(interests)
    return comparands

def comparator(compare_string):
    comparands = {'deleted':set() , 'added': set()}
    soup = BeautifulSoup(compare_string)
    for change_type, css_class in (('deleted', 'diff-deletedline'),('added', 'diff-addedline')):
        changes = set()
        crutons = soup.find_all('td', class_=css_class)
        for cruton in crutons:
            cruton_string = ''.join(list(cruton.strings))
            interests = wikitext_of_interest(cruton_string)
            changes.update(interests)
        comparands[change_type].update(changes)

    uniq_comparands = dict()
    uniq_comparands['added'] = list(comparands['added'].difference(comparands['deleted']))
    uniq_comparands['deleted'] = list(comparands['deleted'].difference(comparands['added']))
    
    return uniq_comparands
    

def make_family(server_name):
    parts = list(map(lambda x: x.lower(), server_name.split('.')))
    if parts[0] == 'commons':
        return ('commons','commons')
    if parts[1] == 'wikidata':
        return ('wikidata', 'wikidata')
    if parts[0] == 'meta':
        return ('meta', 'meta')
    if parts[0] == 'incubator':
        return ('incubator', 'incubator')
    if parts[0] == 'species':
        return ('species', 'species')
    else:
        return parts[0], parts[1]

def get_changes(rcdict):
    '''Get the changes of dois that occured in an rcdict
    @returns dict of lists of 'added' or 'deleted' dois
    or None if there was an error (like deleted history).
    Also handles newly created pages.
    '''
    try:
        server_name = rcdict['server_name']
        lang, fam = make_family(server_name)
        if 'timestamp' in rcdict:
            rcdict['time'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(rcdict['timestamp']))
        #if it's an edit
        logging.error("TYPE" + str(rcdict['type']))
        if rcdict['type'] == 'edit':
            from_rev, to_rev = rcdict['revision']['old'], rcdict['revision']['new']
            logging.error("FROM " + str(from_rev) + " TO " + str(to_rev))
            api_to_hit = pywikibot.Site(lang, fam)
            comparison_response = api_to_hit.compare(from_rev, to_rev)

            logging.error(u"COMPARISON RESPONSE" + str(comparison_response))

            rcdict['doi'] = comparator(comparison_response)
        #if it's a new page
        if rcdict['type'] == 'new':
            title = rcdict['title']
            api_to_hit = pywikibot.Site(lang, fam)
            page = pywikibot.Page(api_to_hit, title)
            rcdict['doi'] = single_comparator(page)
        
        if rcdict['type'] == 'log':
            logging.debug("logging_event" + str(rcdict))
            pass
        else:
            logging.debug('Not an edit, new page, or logging event '+str(rcdict))
            pass
        return rcdict

    except pywikibot.data.api.APIError as e:
        logging.error("API ERROR " + str(e) + str(rcdict))
        return rcdict
    except Exception as e:
        logging.error("EXCEPTION " + str(e) + str(rcdict))
        return rcdict

    