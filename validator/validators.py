# PROJECT : django-contrib-validator
# TIME : 17-9-11 下午3:00
# AUTHOR : Younger Shen
# EMAIL : younger.x.shen@gmail.com
from copy import deepcopy
from django.utils.translation import ugettext as _


class BaseRule:
    name = 'base rule name'
    message = _('i am the base rule, you never see me bro')

    def __init__(self, name, value, *args, message=None):
        self.name = name
        self.value = value
        self.args = args
        self.status = True
        self.message = message if message else self.message

    def check(self):
        raise NotImplementedError

    def get_status(self):
        return self.status

    def get_message(self):
        return self.message


class Required(BaseRule):
    name = 'required'
    message = '{FIELD} is required'

    def check(self):
        self.status = not not self.value

    def get_message(self):
        return self.message.format(FIELD=self.name)


class MetaValidator(type):
    def __new__(mcs, *args, **kwargs):
        name, base, attrs = args
        attrs.update({'validation': mcs.get_attrs(attrs)})
        return super().__new__(mcs, *args)

    @staticmethod
    def get_attrs(attrs):
        return dict((k, v) for k, v in attrs.items() if not k.startswith('__') and isinstance(v, str))


class Validator(metaclass=MetaValidator):

    messages = {}
    info = {}

    default_failed_code = -1
    default_succeed_code = -2

    default_failed_info = _('data is invalid')
    default_succeed_info = _('data is valid')

    def __init__(self, data, request):
        self.data = deepcopy(data)
        self.request = request
        self.status = True
        self.code = -1
        self._message = {}

    def validate(self):
        validation = self._get_validation()
        self._validate(validation)
        self.check() if self.status else None
        return self.status, self.code, self.get_message(), self.get_info()

    def get(self, name, default=None):
        return self.data.get(name, default)

    def check(self):
        self.status = True
        self.code = -2

    def get_info(self):
        if self.default_succeed_code == self.code:
            info = self.default_succeed_info
        elif self.default_failed_code == self.code:
            info = self.default_failed_info
        else:
            info = self.info.get(self.code, '')
        return info

    def get_message(self):
        return self._message

    def set_message(self, name, rule, message):
        self._message.update({name: {}}) if name not in self._message.keys() else None
        self._message[name].update({rule: message})

    def _validate(self, validation):
        for item in validation:
            name = item.get('name', '')
            value = item.get('value', '')
            rules = item.get('rules', [])
            for rule in rules:
                self._check_rule(rule, name, value)

    def _check_rule(self, rule, name, value):
        rule_name = rule.get('name')
        params = rule.get('params')
        rule_class = RULES.get(rule_name)
        message = self.message.get(name, {}).get(rule_name, None)
        rule_instance = rule_class(name, value, *params, message=message)
        rule_instance.check()
        if not rule_instance.get_status():
            self.status = False
            self.set_message(name, rule_name, rule_instance.get_message())

    def _get_validation(self):
        ret = []
        for name, validation in getattr(self, 'validation').items():
            rules = self._get_rules(validation)
            value = self.get(name)
            data = {'name': name, 'value': value, 'rules': list(rules)}
            ret.append(data)
        return ret

    def _get_rules(self, validation):
        rules = map(self._get_rule, validation.split('|'))
        return rules

    @staticmethod
    def _get_rule(rule):
        info = list(map(lambda s: s.strip(), rule.split(':')))
        name = info[0]
        params = map(lambda s: s.strip(), ''.join(info[1:]).split(','))
        rules = {'name': name, 'params': list(params)}
        return rules


RULES = {
    'required': Required
}
