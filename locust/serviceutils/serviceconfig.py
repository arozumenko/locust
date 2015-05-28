#  Copyright (c) 2014 Artem Rozumenko (artyom.rozumenko@gmail.com)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""This module contains global configuration template storage CONFIG_STORAGE.

    This storage instance contains template of any locust module
    configuration files. A locustservice object create configuration
    files at install from configuration template from CONFIG_STORAGE.

    If need you should create configuration template for your module and
    add her to CONFIG_STORAGE at initialisation module for correct
    functionality your locust service utils.

    Module configuration file structure should be like:
          |-----template-----|---section-------------------------|
     cfg = {'<name_template>': [{'section': <section name>,
                                'options': [(<option name>,
                                             <option value>),
                                            (<option name>,
                                            <option value>),...]}],
            '<name_template>': [{'section': <section name>,
                                'options': [(<option name>,
                                             <option value>),
                                            (<option name>,
                                            <option value>),...]}],
            ...}
    Usage:
    CONFIG_STORAGE = ServiceConfig()
    CONFIG_STORAGE.add(cfg)

 """

__author__ = ('Mykhailo Makovetskiy - makovetskiy@gmail.com')

import json
import sys
from copy import deepcopy

from configobj import ConfigObj


class ServiceConfigValidationError(Exception):
    """Validation error of service util configuration instance """
    pass


class ErrMsg(object):
    """Service config error message."""
    #pylint: disable=R0903
    template_type = ('ERROR: Wrong type of configuration template for '
                     'module - {name}. Template type should be '
                     'dictionary\n')

    template_key = ('ERROR. Wrong config format of template for module'
                    '\'{name}\'.Template should  contain one or more '
                    'keys - {keys}. Given template is - {tmpl}.\n')

    template_value = ('ERROR: Wrong type of the \'{conf_name}\' t'
                      'emplate of the module {module}. Type of a config '
                      'template must be list of section dictionaries\n')

    section_type = ('ERROR: A section \'{sect}\' wrong value type of '
                    'the \'{conf_name}\' template of the module '
                    '{module}. Section must describe dictionary like '
                    '{example}.\n')

    section_key = ('ERROR: A section \'{sect}\' wrong format of the \'{'
                   'conf_name}\' template of the module {module}. '
                   'Section should contains the following keys - '
                   '{keys}\n')

    option_type = ('ERROR: Wrong format of an option of section '
                   '\'{sect}\' of the \'{conf_name}\' template of the '
                   'module {module}. Options must be described by list '
                   'of tuples in "options" part of an section '
                   'dictionary.\n Example - {example}.\n')

    template_exist = ('Config template doesn\'t contains template '
                      'for {name}\n')

    cfg_tmpl_key = ('Wrong template name {name}. template name should be '
                    'in - {tmpl_names}\n')


class InfMsg(object):
    """Service config information message."""

    #pylint: disable=R0903
    override_template = ('INFO: Current config {name} is ignored since '
                         'override operation is disabled. Configuration '
                         'template dictionary already contains template '
                         'for {name}.\n')


def confobj_to_bservice_utiltmpl(conf):
    """Simple converter config from confobj.ConfObj to ServiceConfig.

        Args:
          conf (ConfigObj): ConfigObj instance.

        Returns:
          dictionary: dictionary that contains module configs in
            ServiceConfig format.

    """
    if not isinstance(conf, ConfigObj):
        raise TypeError('conf parameter should be ConfObj instance')
    result = []
    sections = conf.sections
    for section in sections:
        items = conf[section].items()
        result.append({'section': section,
                       'options': [(k, v) for k, v in items]})
    return result


class SingletonMeta(type):
    """ Realise singleton pattern."""

    def __init__(cls, name, bases, diction):
        """Constructor."""
        super(SingletonMeta, cls).__init__(name, bases, diction)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls.instance


class ServiceConfig(object):
    """The locust services configurations template storage.

    Configurations templates are stored as dictionary like:
      { <service name>: {'<cfg_name>': [{'section':<section name>,
                                         'options': [(<option name>,
                                                      <option value>),
                                                     (<option name>,
                                                      <option value>),
                                                      ...]}],
                         '<cfg_name>': [{'section': <section name>,
                                         'options': [(<option name>,
                                                      <option value>),
                                                     (<option name>,
                                                      <option value>),
                                                      ...]}],
                         ...},
       ...}

    """
    __metaclass__ = SingletonMeta

    def __init__(self, configs=None):
        """Constructor."""
        configurations = configs or []
        self._conf_tmp = {}
        self._key_list = {'template': ['supervisord', 'config'],
                          'section': ['section', 'options']}
        if isinstance(configurations, list):
            for name, cfg in configurations:
                self.add(name, cfg)
        else:
            msg = ('ERROR: Type \'{type}\' of given configs is wrong. '
                   'Parameter config should be  a list of tupples - '
                   '[(<name>, <config>),..]').format(type=str(type(configs)))
            raise TypeError(msg)

    def get_key_list(self, section):
        """Returns list of valid keys of configuration template.

        Args:
          section (str): Section template config key.

        Returns:
          list: list of valid keys for given section.

        """
        return self._key_list[section] if section in self._key_list else []

    def is_key_in_section(self, section, key):
        """ Check if given key presents in section valid keys.

        Args:
          section (str): Template config section key.
          key (str): Key value.

        Returns:
          bool: True if key present in section valid keys list.

        """
        return key in self._key_list[section]

    def add_templalate_key(self, section, key):
        """Add custom key to valid key list.

        Args:
          section (str): Template config section key.
          key (str): Key value.

        """
        self._key_list[section].append(str(key))

    def isconfigvalid(self, config_name, stderr=True):
        """Check is configurations template in internal storage valid.

        Args:
          config_name (str): Template config key.
          key (str): Key value.
          stderr (bool): Set quiet check validation if False.

        Returns:
          bool: True if configurations template is valid else False.

        """
        tmpl = self.get_allconfigs(config_name)
        try:
            if not tmpl:
                msg = ErrMsg.template_exist.format(path=config_name)
                raise ServiceConfigValidationError(msg)
            self.validate_cfg_template(config_name, tmpl)
        except (ValueError, ServiceConfigValidationError) as err:
            sys.stderr.write(err if stderr else '')
            return False
        return True

    def validate_cfg_template(self, module_name, config_tmpl):
        """Validate is a given dictionary valid configuration template.

        This method use to convert AssertionError to
        ServiceConfigValidationError error if given dictionary
        is not valid configuration template.
        Args:
          module_name (str): Template config key(name).
          config_tmpl (dict): Configuration template dictionary.

        Raises:
          ServiceConfigValidationError: Raises if given dictionary isn't
           valid configuration template.

        """
        try:
            self._validate_cfg_template(module_name, config_tmpl)
        except AssertionError as err:
            raise ServiceConfigValidationError(err.message)

    def _validate_cfg_template(self, module_name, config_tmpl):
        """Validate is a given dictionary valid configurations template.

        Args:
          module_name (str): Configurations template name(key).
          config_tmpl (dict): Configurations template dictionary.

        Raises:
          AssertionError: Raises if given dictionary isn't
           valid configurations template.

        """
        assert isinstance(config_tmpl, dict), ErrMsg.template_type.format(
            str(type(config_tmpl)))

        chk = self._check_keys
        assert chk(config_tmpl, 'template'), ErrMsg.template_key.format(
            name=module_name, tmpl=json.dumps(config_tmpl),
            keys=', '.join(self._key_list['template_keys']))

        for cfg_name, cfg_value in config_tmpl.items():
            assert isinstance(cfg_value, list), ErrMsg.template_value.format(
                conf_name=cfg_name, module=module_name)
            for sect in cfg_value:
                self._validate_config_section(module_name, cfg_name, sect)

    def _check_keys(self, dictionary, keys_section, condition='any'):
        """Check are keys in given dictionary valid.

        Args:
          dictionary (dict): Configuration template dictionary.
          keys_section (str): Key. Describe is valid key list use to
           check.
          condition (str, option): Set the condition check.


        Returns:
          bool: True if keys are valid else False.

        """
        cond = all if condition == 'all' else any
        return cond(n in dictionary for n in self._key_list[keys_section])

    def _validate_config_section(self, module_name, config_name, section):
        """Validate is a given dictionary valid configuration template.

        Args:
          module_name (str): Configurations template name(key).
          config_name (str): Configuration template name(key).
          section (dict): Configuration template dictionary.

        Raises:
          AssertionError: Raises if given dictionary isn't
           valid configuration template.

        """
        dict_examp = ('{\'section\': \'<name>\', \'options\': '
                      '[(\'<name>\', \'<value>\'), (\'<name_1>\','
                      ' \'<value_1>\')]}')

        assert isinstance(section, dict), ErrMsg.section_type.format(
            conf_name=config_name, module=module_name,
            example=dict_examp, sect='Unknown')

        chk = self._check_keys
        assert chk(section, 'section', 'all'), ErrMsg.section_key.format(
            conf_name=config_name, module=module_name,
            keys=', '.join(self._key_list['section']), sect='Unknown')

        msg = ErrMsg.option_type.format(conf_name=config_name,
                                        module=module_name,
                                        example=dict_examp,
                                        sect=section['section'])
        assert isinstance(section['options'], list), msg
        for opt in section['options']:
            assert isinstance(opt, tuple), ErrMsg.option_type.format(
                conf_name=config_name, module=module_name, example=dict_examp,
                sect=section['section'])

            assert 2 == len(opt), ErrMsg.option_type.format(
                conf_name=config_name, module=module_name, example=dict_examp,
                sect=section['section'])

    def add(self, name, template, override=False, stderr=True):
        """Add own custom dictionary to the configurations templates.

        Args:
          name (str): Service name.
          config_name (str): Configuration template name(key).
          template (dict): Configurations template dictionary.
          override (bool, optional): If True allow override exist
           configurations templates of given service.
          stderr (bool): Set quiet operation.

        """
        try:
            self.validate_cfg_template(name, template)

            if str(name) in self._conf_tmp and not override:
                if stderr:
                    sys.stdout.write(
                        InfMsg.override_template.format(name=name))
            else:
                self._conf_tmp[str(name)] = deepcopy(template)
        except ServiceConfigValidationError as err:
            sys.stderr.write(err if stderr else '')

    def remove(self, service_name):
        """Remove configurations template from local storage.

        Args:
          service_name (str): Service name.

        """
        if service_name in self._conf_tmp:
            del self._conf_tmp[service_name]

    def get_allconfigs(self, service_name):
        """Get configurations template for given service.

        Args:
          service_name (str): Service name.

        Returns:
          dict, None: Configurations template dictionary for given
           service or None if isn't exist.

        """
        return (self._conf_tmp[service_name] if service_name in
                self._conf_tmp else None)

    def get_config(self, service_name, conf_name, stderr=True):
        """Get configuration template for given service.

        Args:
          service_name (str): Service name.
          conf_name (str): Configuration name.
          stderr (bool): Set quiet operation.

        Returns:
          dict, None: Configuration template dictionary for given
           service name and config name or None if isn't exist.

        """
        tmpl = self.get_allconfigs(service_name)
        key_list = self._key_list['template']
        if conf_name not in key_list and stderr:
            sys.stderr.write(ErrMsg.cfg_tmpl_key.format(
                name=service_name, tmpl_names=', '.join(key_list)))

        return tmpl[conf_name] if conf_name in tmpl else None
