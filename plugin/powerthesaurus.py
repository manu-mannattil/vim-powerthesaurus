#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# WIP script to integrate powerthesaurus.org with Vim.
#
# TODO:
#
# 1. Simplify GQL queries
# 2. Right align part of speech
# 3. new vim keyword thesaurusfunc -- https://github.com/vim/vim/issues/8950 that handles some of
# the plugin's features

import re
import sys
import requests

API_URL = r"https://api.powerthesaurus.org"

HEADERS = {
    "content-type": "application/json",
    "Origin": "https://www.powerthesaurus.org",
    "Referer": "https://www.powerthesaurus.org",
    "User-Agent": "Mozilla/5.0 (compatible)"
}

GQL_TERM_QUERY = r"""
query TERM_QUERY($term: String!) {
  term(slugEqual: $term) {
    has_abbreviations
    counters
    name
    slug
    rating_min_good
    id
    isFavorite
    inflected {
      name
      id
      slug
      counters
      __typename
    }
    images
    isBad
    __typename
  }
}"""

GQL_THESAURUS_QUERY = r"""
query THESAURUSES_QUERY($after: String, $first: Int, $before: String, 
                        $last: Int, $termID: ID!, $list: List!, 
                        $sort: ThesaurusSorting!, $tagID: Int, 
                        $posID: Int, $syllables: Int, $type: Type) {
  thesauruses(
    termId: $termID
    sort: $sort
    list: $list
    after: $after
    first: $first
    before: $before
    last: $last
    tagId: $tagID
    partOfSpeechId: $posID
    syllables: $syllables
    type: $type
  ) {
    limit
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
      __typename
    }
    edges {
      node {
        _type
        id
        isPinned
        targetTerm {
          id
          name
          slug
          __typename
        }
        relations
        rating
        vote {
          voteType
          id
          __typename
        }
        votes
        __typename
      }
      __typename
    }
    __typename
  }
}"""

PARTS_OF_SPEECH = [
    "adjective",
    "noun",
    "pronoun",
    "adverb",
    "idiom",
    "verb",
    "interjection",
    "phrase",
    "conjunction",
    "preposition",
    "phrasal verb",
]

PARTS_OF_SPEECH_SHORT = [
    "adj.", "n.", "pr.", "adv.", "idi.", "v.", "int.", "phr.", "conj.", "prep.", "phr. v."
]

class PowerThesaurus:

    def term_id(self, term):
        params = {
            "operationName": "TERM_QUERY", "variables": {
                "term": term
            }, "query": GQL_TERM_QUERY
        }

        r = requests.post(API_URL, json=params, headers=HEADERS)
        term = r.json()["data"]["term"]

        if term:
            return term["id"]
        else:
            return None

    def thesaurus(self, term, kind="synonym"):
        term_id = self.term_id(term)
        if not term_id:
            return None

        params = {
            "operationName": "THESAURUSES_QUERY",
            "variables": {
                "termID": term_id,
                "sort": {
                    "field": "RATING", "direction": "DESC"
                },
                "limit": 50,
                "syllables": None,
                "list": kind.upper(),
                "posID": None,
                "query": None,
                "tagID": None,
                "first": 50,
                "after": ""
            },
            "query": GQL_THESAURUS_QUERY
        }

        r = requests.post(API_URL, json=params, headers=HEADERS)

        for res in r.json()["data"]["thesauruses"]["edges"]:
            yield {
                "name": res["node"]["targetTerm"]["name"],
                "pos": res["node"]["relations"]["parts_of_speech"],
            }

    @staticmethod
    def vim_menu(results, pos_short=True):
        items = []

        for r in results:
            name = r["name"]
            pos = r["pos"]

            if pos:
                if pos_short:
                    pos = ", ".join(PARTS_OF_SPEECH_SHORT[_ - 1] for _ in pos)
                else:
                    pos = ", ".join(PARTS_OF_SPEECH[_ - 1] for _ in pos)
                pos = f"[{pos}]"
            else:
                pos = ""

            items.append(f"{{ 'word': {repr(name)}, 'menu': {repr(pos)} }}")

        return items

if __name__ == "__main__":
    pt = PowerThesaurus()
    query = " ".join(sys.argv[1:]).strip()
    query = re.sub(r"[^\w ]+", "", query)

    for item in pt.vim_menu(pt.thesaurus(query)):
        print(item)
