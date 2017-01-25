import time
import logging
import collections
import operator

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


class BiorxivCrawler(object):
    def __init__(self, driver):
        self.driver = driver

    def extract_links(self, page):
        self.driver.get(page)
        elements = self.driver.find_elements_by_class_name("highwire-cite-linked-title")
        return [elem.get_attribute("href") for elem in elements]

    def get_all_links(self, filename=None, sleep_every=10, sleep_for=10.0):
        '''
        Yield links and optionally write them to a file.

        Parameters
        ----------
        filename : str or None
            Where to store the collected links (or ``None``, the default, to not
            store them at all).
        sleep_every : int
            Make a pause (to rate-limit our access) after this many pages.
        sleep_for : float
            Make a pause of this length.

        Returns
        ------
        links : list of str
            A list of links to a biorxiv page.
        '''
        if filename is not None:
            f = open(filename, 'w')
        self.driver.get("http://biorxiv.org/content/early/recent")
        last_page = int(self.driver.find_element_by_class_name("pager-last").text)
        page_counter = 0
        links = []
        while page_counter < last_page:
            page_links = self.extract_links("http://biorxiv.org/content/early/recent?page=" + str(page_counter))
            if filename is not None:
                f.write('\n'.join(page_links) + '\n')
            links.extend(page_links)
            page_counter += 1
            if (page_counter % sleep_every) == 0:
                logger.info('%d pages... (sleeping for %.1fs)' % (page_counter, sleep_for))
                time.sleep(sleep_for)
        if filename is not None:
            f.close()
        return links

    def extract_journal_from_page(self, link):
        self.driver.get(link)
        time.sleep(6)
        try:
            elem = self.driver.find_element_by_class_name("pub_jnl")
            out = elem.text
        except NoSuchElementException:
            out = "unpublished"
        fields = out.split(' ')
        try:
            out = ' '.join(fields[3:fields.index("doi:")])
        except ValueError:
            out = "unpublished"
        return out

if __name__ == '__main__':
    import os
    crawler = BiorxivCrawler(webdriver.PhantomJS())

    # links = crawler.get_all_links('myCrawlerLinks.txt')  # comment if you have already a list of links

    with open("myCrawlerLinks.txt", "r") as infile: # uncomment if you have already a list of links
        links = infile.read().splitlines()  # uncomment if you have already a list of links

    with open("linkPublishedIn.txt", "w", buffering=1) as outfile:
        journal_counter = collections.defaultdict(int)
        for link in links:
            journal = crawler.extract_journal_from_page(link)
            outfile.write(link + '\t' + journal + '\n')
            if journal:
                journal_counter[journal] += 1
    crawler.driver.close()

    for journal, counter in sorted(journal_counter.items(),
                                   key=operator.itemgetter(1), reverse=True):
        print '\t'.join([journal, str(counter)])
