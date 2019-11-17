import os
import sys
import requests
import json
from pystrict import strict
from typing import List, Set, Dict, Tuple, Optional, Any, Union
from enum import Enum, unique
from urllib.parse import quote_plus
from pprint import pprint

path = os.path.abspath(os.path.dirname(__file__))
(head, tail)  = os.path.split(path)
if not head in sys.path:
    sys.path.append(head)
if not path in sys.path:
    sys.path.append(path)

from models.Helpers import Languages, Actions, LangString, BaseError
from models.Connection import Connection

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


@strict
class KnoraProject:
    SYSTEM_PROJECT: str = "http://www.knora.org/ontology/knora-admin#SystemProject"
    _id: str
    _shortcode: str
    _shortname: str
    _longname: str
    _description: LangString
    _keywords: Set[str]
    _ontologies: Set[str]
    _selfjoin: bool
    _status: bool
    _logo: Optional[str]
    changed: Set[str]

    def __init__(self,
                 con:  Connection,
                 id: Optional[str] = None,
                 shortcode: Optional[str] = None,
                 shortname: Optional[str] = None,
                 longname: Optional[str] = None,
                 description: Optional[LangString] = LangString(),
                 keywords: Optional[Set[str]] = None,
                 ontologies: Optional[Set[str]] = None,
                 selfjoin: Optional[bool] = None,
                 status: Optional[bool] = None,
                 logo: Optional[str] = None):
        if not isinstance(con, Connection):
            raise BaseError ('"con"-parameter must be an instance of Connection')
        self.con = con
        self._id = str(id) if id is not None else None
        self._shortcode = str(shortcode) if shortcode is not None else None
        self._shortname = str(shortname) if shortname is not None else None
        self._longname = str(longname) if longname is not None else None
        if not isinstance(description, LangString) and description is not None:
            raise BaseError('Description must be LangString instance or None!')
        self._description = description
        if not isinstance(keywords, set) and keywords is not None:
            raise BaseError('Keywords must be a set of strings or None!')
        self._keywords = keywords
        if not isinstance(ontologies, set) and ontologies is not None:
            raise BaseError('Ontologies must be a set of strings or None!')
        self._ontologies = ontologies
        self._selfjoin = bool(selfjoin) if selfjoin is not None else None
        self._status = bool(status) if status is not None else None
        self._logo = str(logo) if logo is not None else None
        self.changed = set()

    def __str__(self):
        tmpstr = self._id + "\n  " + self._shortcode + "\n  " + self._shortname
        return tmpstr

    @property
    def id(self) -> Optional[str]:
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        raise BaseError('Project id cannot be modified!')

    @property
    def shortcode(self) -> Optional[str]:
        return self._shortcode

    @shortcode.setter
    def shortcode(self, value: str) -> None:
        raise BaseError('Shortcode id cannot be modified!')

    @property
    def shortname(self) -> Optional[str]:
        return self._shortname

    @shortname.setter
    def shortname(self, value: str) -> None:
        self._shortname = str(value)
        self.changed.add('shortname')

    @property
    def longname(self) -> Optional[str]:
        return self._longname

    @longname.setter
    def longname(self, value: str) -> None:
        self._longname = str(value)
        self.changed.add('longname')

    @property
    def description(self) -> Optional[LangString]:
        return self._description

    @description.setter
    def description(self, value: LangString) -> None:
        self._descriptions = value
        self.changed.add('description')

    def addDescription(self, lang: Union[Languages, str], value) -> None:
        if isinstance(lang, Languages):
            self._descriptions[lang] = value
            self.changed.add('description')
        else:
            lmap = dict(map(lambda a: (a.value, a), Languages))
            if lmap.get(lang) is None:
                raise BaseError('Invalid language string "' + lang  + '"!')
            self._description[lmap[lang]] = value
            self.changed.add('description')

    def rmDescription(self, lang: Union[Languages, str]) -> None:
        if isinstance(lang, Languages):
            del self._description[lang]
            self.changed.add('description')
        else:
            lmap = dict(map(lambda a: (a.value, a), Languages))
            if lmap.get(lang) is None:
                raise BaseError('Invalid language string "' + lang  + '"!')
            del self._description[lmap[lang]]
            self.changed.add('description')

    @property
    def keywords(self) -> Set[str]:
        return self._keywords

    @keywords.setter
    def keywords(self, value: Set[str]):
        if isinstance(value, set):
            self_.keywords = value
            self.changed.add('keywords')
        else:
            raise BaseError('Must be a set of strings!')

    def add_keyword(self, value: str):
        self._keywords.add(value)
        self.changed.add('keywords')

    def rm_keyword(self, value: str):
        try:
            self._keywords.remove(value)
        except KeyError as ke:
            raise BaseError('Keyword "'  + value + '" is not in keyword set')
        self.changed.add('keywords')

    @property
    def ontologies(self) -> Set[str]:
        return self._ontologies

    @ontologies.setter
    def ontologies(self, value: Set[str]) -> None:
        raise BaseError('Cannot add a ontology!')

    @property
    def selfjoin(self) -> Optional[bool]:
        return self._selfjoin

    @selfjoin.setter
    def selfjoin(selfself, value: bool) ->  None:
        if self._selfjoint != value:
            self.changed.add('selfjoin')
        self._selfjoin = value

    @property
    def status(self) -> bool:
        return self._status

    @status.setter
    def status(self, value: bool) -> None:
        self._status = value
        self.changed.add('status')

    @property
    def logo(self) -> str:
        return self._logo

    @logo.setter
    def logo(self, value: str) -> None:
        self._logo = value
        self.changed.add('logo')

    @classmethod
    def fromJsonObj(cls, con: Connection, json_obj: Any):
        id = json_obj.get('id')
        if id is None:
            raise BaseError('Project id is missing')
        shortcode = json_obj.get('shortcode')
        if shortcode is None:
            raise BaseError("Shortcode is missing")
        shortname = json_obj.get('shortname')
        if shortname is None:
            raise BaseError("Shortname is missing")
        longname = json_obj.get('longname')
        if longname is None:
            raise BaseError("Longname is missing")
        descr = json_obj.get('description')
        if descr is not None:
            description = LangString()
            for d in descr:
                description[d['language'] if d.get('language') is not None else 'en'] = d['value']
        else:
            description = None
        keywords = set(json_obj.get('keywords'))
        if keywords is None:
            raise BaseError("Keywords are missing")
        ontologies = set(json_obj.get('ontologies'))
        if ontologies is None:
            raise BaseError("Keywords are missing")
        selfjoin = json_obj.get('selfjoin')
        if selfjoin is None:
            raise BaseError("Selfjoin is missing")
        status = json_obj.get('status')
        if status is None:
            raise BaseError("Status is missing")
        logo = json_obj.get('logo')
        return cls(con=con,
                   id=id,
                   shortcode=shortcode,
                   shortname=shortname,
                   longname=longname,
                   description=description,
                   keywords=keywords,
                   ontologies=ontologies,
                   selfjoin=selfjoin,
                   status=status,
                   logo=logo)

    def toJsonObj(self, action: Actions):
        tmp = {}
        if action == Actions.Create:
            if self._shortcode is None:
                raise BaseError("There must be a valid project shortcode!")
            tmp['shortcode'] = self._shortcode
            if self._shortname is None:
                raise BaseError("There must be a valid project shortname!")
            tmp['shortname'] = self._shortname
            if self._longname is  None:
                raise BaseError("There must be a valid project longname!")
            tmp['longname'] = self._longname
            if self._description.isEmpty():
                raise BaseError("There must be a valid project description!")
            tmp['description'] = self._description.toJsonObj()
            if len(self._keywords) > 0:
                tmp['keywords'] = self._keywords
            if self._selfjoin is None:
                raise BaseError("selfjoin must be defined (True or False!")
            tmp['selfjoin'] = self._selfjoin
            if self._status is None:
                raise BaseError("status must be defined (True or False!")
            tmp['status'] = self._status
        elif action == Actions.Update:
            if self._shortcode is not None and 'shortcode' in self.changed:
                tmp['shortcode'] = self._shortcode
            if self._shortname is not None  and 'shortname' in self.changed:
                tmp['shortname'] = self._shortname
            if self._longname is not None and 'longname' in self.changed:
                tmp['longname'] = self._longname
            if not self._description.isEmpty() and 'description' in self.changed:
                tmp['description'] = self._description.toJsonObj()
            if len(self._keywords) > 0 and 'keywords' in self.changed:
                tmp['keywords'] = self._keywords
            if self._selfjoin is not None and 'selfjoin' in self.changed:
                tmp['selfjoin'] = self._selfjoin
            if self._status is not None and 'status' in self.changed:
                tmp['status'] = self._status
        return tmp

    def create(self):
        jsonobj = self.toJsonObj(Actions.Create)
        jsondata = json.dumps(jsonobj, cls=SetEncoder)
        result = self.con.post('/admin/projects', jsondata)
        return KnoraProject.fromJsonObj(self.con, result['project'])

    def read(self):
        result = self.con.get('/admin/projects/iri/' + quote_plus(self._id))
        return KnoraProject.fromJsonObj(self.con, result['project'])

    def update(self):
        jsonobj = self.toJsonObj(Actions.Update)
        if jsonobj:
            jsondata = json.dumps(jsonobj, cls=SetEncoder)
            result = self.con.put('/admin/projects/iri/' + quote_plus(self.id), jsondata)
            return KnoraProject.fromJsonObj(self.con, result['project'])
        else:
            return None

    def delete(self):
        result = self.con.delete('/admin/projects/iri/' + quote_plus(self._id))
        return result

    @staticmethod
    def getAllProjects(con: Connection):
        result = con.get('/admin/projects')
        if 'projects' not in result:
            raise BaseError("Request got no projects!")
        return list(map(lambda a: KnoraProject.fromJsonObj(con, a), result['projects']))

    def print(self):
        print('Project Info:')
        print('  Id:         {}'.format(self._id))
        print('  Shortcode:  {}'.format(self._shortcode))
        print('  Shortname:  {}'.format(self._shortname))
        print('  Longname:   {}'.format(self._longname))
        if self._description is not None:
            print('  Description:')
            for descr in self._description.items():
                print('    {}: {}'.format(descr[0], descr[1]))
        else:
            print('  Description: None')
        if self._keywords is not None:
            print('  Keywords:   {}'.format(' '.join(self._keywords)))
        else:
            print('  Keywords:   None')
        if self._ontologies is not None:
            print('  Ontologies: {}'.format(' '.join(self._ontologies)))
        else:
            print('  Ontologies: None')
        print('  Selfjoin:   {}'.format(self._selfjoin))
        print('  Status:     {}'.format(self._status))

if __name__ == '__main__':
    con = Connection('http://0.0.0.0:3333')
    con.login('root@example.com', 'test')

    projects = KnoraProject.getAllProjects(con)

    for project in projects:
        project.print()

    print('==============================================================')

    new_project = KnoraProject(con=con,
                               shortcode='F11F',
                               shortname='mytest3',
                               longname='A Test beloning to me',
                               description=LangString({Languages.EN: 'My Tests description'}),
                               keywords={'AAA', 'BBB'},
                               selfjoin=False,
                               status=True).create()

    new_project.print()

    new_project.longname = 'A long name fore a short project'
    new_project.status = False
    new_project.description = LangString({Languages.DE: 'Beschreibung meines Tests'})
    new_project.add_keyword('CCC')
    new_project = new_project.update()
    new_project.print()

    new_project =  new_project.delete()

    print('**************************************************************')
    projects = KnoraProject.getAllProjects(con)

    for project in projects:
        project.print()
