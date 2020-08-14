# -*- coding: utf-8 -*-
from typing import Union
import requests
from lxml import html
from lxml.html import HtmlElement
import logging

__author__ = "Linus Kohl"


class Document():

    def __init__(self, number: str):
        """
        Args:
            number (str): Hostname
        Raises:
            InvalidUrl: If hostname is not set
        """
        self.data = {}
        url = f"https://patents.google.com/patent/{number}/en"
        response = requests.get(url)
        if response.ok:
            self.data = self.__process(response.content)
        else:
            raise Exception("Something went wrong getting the document")

    def __get(self, doc: HtmlElement, xpath: str, many: bool = False) -> Union[
        HtmlElement, str, list, None]:
        """ Processes xpath queries on the document tree
        Args:
            doc (HtmlElement): Root element
            xpath (str): XPath selector
            many (bool): Expect multiple results, default: False
        Returns:
            HtmlElement|str|list|None: The result of the query
        """
        try:
            res = doc.xpath(xpath)
            if many:
                return res
            else:
                if isinstance(res, list):
                    return res[0]
                else:
                    return res
        except:
            logging.info(f"XPath query failed: {xpath}")
            if many:
                return []
            else:
                return None

    def __get_cpcs(self, doc: HtmlElement) -> list:
        """ Extracts CPC codes from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with attributes cpc, first_code
        """
        cpcs = []
        for element in self.__get(doc, "//li[@itemprop='cpcs']", many=True):
            cpc = {}
            cpc['first_code'] = True if \
                self.__get(element, ".//meta[@itemprop='FirstCode']/@content") == "true" else False
            cpc['cpc'] = self.__get(element, ".//span[@itemprop='Code']/text()")
            cpcs.append(cpc)
        # remove duplicates
        unique = [dict(t) for t in {tuple(d.items()) for d in cpcs}]
        return unique

    def __get_description(self, doc: HtmlElement) -> str:
        """ Extracts long description from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            str: Description from patent
        """
        description = ""
        for element in self.__get(doc, "//section[@itemprop='description']/div[@itemprop='content']/descendant::*", many=True):
            if element.text:
                description += element.text
            if element.tag == "heading":
                description += "\n\n"
            elif element.tag == "li":
                description += "\n"
        description = description.strip()
        return description

    def __get_dates(self, doc: HtmlElement) -> list:
        """ Extracts dates from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes date, type
        """
        dates = []
        for date_element in self.__get(doc, "//meta[@name='DC.date']", many=True):
            date = {}
            date['date'] = date_element.attrib.get('content')
            date['type'] = date_element.attrib.get('scheme') or ''
            dates.append(date)
        return dates

    def __get_claims(self, doc: HtmlElement) -> list:
        """ Extracts claims from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes number, text, dependent
        """
        claims = []
        claim_section = self.__get(doc, "//section[@itemprop='claims']")
        if claim_section is not None:
            for claim in self.__get(claim_section, ".//div[@itemprop='content'][1]/*[contains(@class, 'claims')]/*[contains(@class, 'claim')]", many=True):
                claim_obj = {}
                claim_obj['dependent'] = True if claim.get('class') == "claim-dependent" else False
                claim_obj['number'] = int(self.__get(claim, "./div[contains(@class,'claim')][1]/@num"))
                text = "".join(claim.xpath("./descendant::*/text()"))
                claim_obj['text'] = text.strip() if text else None
                claims.append(claim_obj)
        return claims

    def __get_priority_claims(self, doc: HtmlElement) -> list:
        """ Extracts priority claims from patents
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes title, filingDate, priorityDate
        """
        priority_claims = []
        for row in self.__get(doc, "//tr[@itemprop='appsClaimingPriority']", many=True):
            priority_claim = {}
            priority_claim['filingDate'] = self.__get(row, ".//td[@itemprop='filingDate']/text()")
            priority_claim['priorityDate'] = self.__get(row, ".//td[@itemprop='priorityDate']/text()")
            priority_claim['title'] = self.__get(row, ".//td[@itemprop='title']/text()")
            priority_claims.append(priority_claim)
        return priority_claims

    def __get_priority_applications(self, doc: HtmlElement) -> list:
        """ Extracts priority applications from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes applicationNumber, isUsProvisional, filingDate, priorityDate
        """
        priority_applications = []
        for row in self.__get(doc, "//tr[@itemprop='priorityApps']", many=True):
            application = {}
            application['filingDate'] = self.__get(row, ".//td[@itemprop='filingDate']/text()")
            application['priorityDate'] = self.__get(row, ".//td[@itemprop='priorityDate']/text()")
            application['title'] = self.__get(row, ".//td[@itemprop='title']/text()")
            content_element = self.__get(row, ".//td[1]")
            application['applicationNumber'] = self.__get(content_element, ".//span[@itemprop='applicationNumber']/text()")
            application['isUsProvisional'] = self.__get(content_element, ".//span[@itemprop='isUsProvisional']/text()")
            priority_applications.append(application)
        return priority_applications

    def __get_events(self, doc: HtmlElement) -> list:
        """ Extracts events from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes title, time, type, critical
        """
        events = []
        for row in self.__get(doc, "//dd[@itemprop='events']", many=True):
            event = {}
            event['time'] = self.__get(row, ".//time[@itemprop='date']/text()")
            event['title'] = self.__get(row, ".//span[@itemprop='title']/text()")
            event['type'] = self.__get(row, ".//span[@itemprop='type']/text()")
            event['critical'] = True if self.__get(row, ".//span[@itemprop='critical']/text()") == 'Critical' else False
            events.append(event)
        return events

    def __get_legal_events(self, doc: HtmlElement) -> list:
        """ Extracts legal events from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes date, code, title, content {title, text}
        """
        events = []
        for row in self.__get(doc, "//tr[@itemprop='legalEvents']", many=True):
            event = {}
            event['date'] = self.__get(row, ".//td/time[@itemprop='date']/text()")
            event['code'] = self.__get(row, ".//td[@itemprop='code']/text()")
            event['title'] = self.__get(row, ".//td[@itemprop='title']/text()")
            content = []
            content_element = self.__get(row, ".//td[4]")
            for p in self.__get(content_element, ".//p", many=True):
                cont = {}
                cont['title'] = self.__get(p, ".//strong/text()")
                cont['text'] = self.__get(p, ".//span/text()")
                content.append(cont)
            event['content'] = content
            events.append(event)
        return events

    def __get_similar_documents(self, doc: HtmlElement) -> list:
        """ Extracts similar documents from patent
        Args:
            doc (HtmlElement): Root element
        Returns:
            list: List containing dictionaries with the attributes date, title, isPatent, publicationNumber, primaryLanguage
        """
        similar_documents = []
        for row in self.__get(doc, "//tr[@itemprop='similarDocuments']", many=True):
            document = {}
            document['date'] = self.__get(row, ".//time[@itemprop='publicationDate']/text()")
            title = self.__get(row, ".//td[@itemprop='title']/text()")
            document['title'] = title.strip() if title else None
            content_element = self.__get(row, ".//td[1]")
            if content_element is not None:
                document['isPatent'] = True if self.__get(content_element, ".//meta[@itemprop='isPatent']/@content") == 'true' else False
                document['publiationNumber'] = self.__get(content_element, ".//span[@itemprop='publicationNumber']/text()")
                document['primaryLanguage'] = self.__get(content_element, ".//span[@itemprop='primaryLanguage']/text()")
            similar_documents.append(document)
        return similar_documents

    def __get_citations(self, doc: HtmlElement, direction: str) -> list:
        """ Extracts citations from patent
        Args:
            doc (HtmlElement): Root element
            direction (str): Type of citations forward|backward
        Returns:
            list: List containing dictionaries with the attributes priorityDate, publicationDate, assigneeOriginal, title,
                  examinerCited, publicationNumber, primaryLanguage
        """
        citations = []
        itemprop = ""
        if direction == "forward":
            itemprop = "forwardReferencesOrig"
        elif direction == "backward":
            itemprop = "backwardReferencesOrig"
        for row in self.__get(doc, "//tr[@itemprop='{}']".format(itemprop),
                              many=True):
            citation = {}
            citation['priorityDate'] = self.__get(row, ".//td[@itemprop='priorityDate']/text()")
            citation['publicationDate'] = self.__get(row, ".//td[@itemprop='publicationDate']/text()")
            assigneeOriginal = self.__get(row, ".//td/span[@itemprop='assigneeOriginal']/text()")
            citation['assigneeOriginal'] = assigneeOriginal.strip() if assigneeOriginal else None
            title = self.__get(row, ".//td[@itemprop='title']/text()")
            citation['title'] = title.strip() if title else None
            content_element = self.__get(row, ".//td[1]")
            if content_element is not None:
                citation['examinerCited'] = True if self.__get(content_element, ".//span[@itemprop='examinerCited']/text()") == "*" else False
                citation['publiationNumber'] = self.__get(content_element, ".//span[@itemprop='publicationNumber']/text()")
                citation['primaryLanguage'] = self.__get(content_element, ".//span[@itemprop='primaryLanguage']/text()")
            citations.append(citation)
        return citations

    def __process(self, content: bytes) -> dict:
        """ Process patent
        Args:
            content (bytes): HTML document of the patent
        Returns:
            list: List containing dictionaries with the attributes priorityDate, publicationDate,
                  assigneeOriginal, title, examinerCited, publicationNumber, primaryLanguage
        """
        doc = html.fromstring(content)
        data = {}
        data['inventors'] = self.__get(doc, "//meta[@name='DC.contributor' and @scheme='inventor']/@content", many=True)
        data['assignee'] = self.__get(doc, "//meta[@name='DC.contributor' and @scheme='assignee']/@content", many=True)
        data['type'] = self.__get(doc, "//meta[@name='DC.type']/@content")
        title = self.__get(doc, "//meta[@name='DC.title']/@content")
        data['title'] = title.strip() if title else None
        description = self.__get(doc, "//meta[@name='DC.description']/@content")
        data['description'] = description.strip() if description else None
        data['abstract'] = self.__get(doc, "//section[@itemprop='abstract']/div[@itemprop='content']/descendant::*/text()", many=True)
        data['abstract'] = "".join([p.strip() for p in data['abstract']])
        countryCode = self.__get(doc, "//dd[@itemprop='countryCode']/text()")
        data['countryCode'] = countryCode.strip() if countryCode else None
        countryName = self.__get(doc, "//dd[@itemprop='countryName']/text()")
        data['countryName'] = countryName.strip() if countryName else None
        data['citation_patent_application_number'] = self.__get(doc, "//meta[@name='citation_patent_application_number']/@content")
        data['citation_pdf_url'] = self.__get(doc, "//meta[@name='citation_pdf_url']/@content")
        data['citation_patent_publication_number'] = self.__get(doc, "//meta[@name='citation_patent_publication_number']/@content")
        data['relations'] = self.__get(doc, "//meta[@name='DC.relation']/@content", many=True)
        # call extraction functions
        data['cpcs'] = self.__get_cpcs(doc)
        data['description_alt'] = self.__get_description(doc)
        data['dates'] = self.__get_dates(doc)
        data['claims'] = self.__get_claims(doc)
        data['priority_claims'] = self.__get_priority_claims(doc)
        data['priority_applications'] = self.__get_priority_applications(doc)
        data['events'] = self.__get_events(doc)
        data['legal_events'] = self.__get_legal_events(doc)
        data['similar_documents'] = self.__get_similar_documents(doc)
        data['forward_citations'] = self.__get_citations(doc, "forward")
        data['backward_citations'] = self.__get_citations(doc, "backward")
        return data