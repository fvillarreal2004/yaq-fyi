"""Construct a graph of trait and daemon relationships."""


import os
import pathlib
import copy
import collections
import toml
import json


__here__ = pathlib.Path(__file__).resolve().parent


# trait -------------------------------------------------------------------------------------------


class Trait(object):
    def __init__(self, **kwargs):
        self.trait = kwargs["trait"]
        self.name = self.trait
        self.doc = kwargs["doc"]
        self.requires = dict()
        for r in kwargs["requires"]:
            self.requires[r] = []
        self.config = kwargs.get("config", dict())
        self.state = kwargs.get("state", dict())
        self.method = kwargs.get("method", dict())
        self.daemons = dict()

    def __repr__(self):
        return self.name

    def format_origin(self, lis):
        return "from " + " ➜ ".join([f"<a href='../{l}'>{l}</a>" for l in lis])


traits = {}

# initialize
for name in os.listdir(__here__ / "traits"):
    dic = toml.load(__here__ / "traits" / name)
    t = Trait(**dic)
    traits[t.trait] = t

# sort
traits = collections.OrderedDict(sorted(traits.items()))

# populate
todo = []
for t in traits.values():
    for k, v in t.requires.items():
        todo.append((t, k, v))
while todo:
    t, k, v = todo.pop(0)
    if k not in t.requires.keys():
        t.requires[k] = v
    # config
    for name, config in traits[k].config.items():
        if name not in t.config.keys():
            t.config[name] = copy.deepcopy(config)
            t.config[name]["origin"] = v + [k] + config.get("origin", [])
    # state
    for name, state in traits[k].state.items():
        if name not in t.state.keys():
            t.state[name] = copy.deepcopy(state)
            t.state[name]["origin"] = v + [k] + state.get("origin", [])
    # method
    for name, method in traits[k].method.items():
        if name not in t.method.keys():
            t.method[name] = copy.deepcopy(method)
            t.method[name]["origin"] = v + [k] + method.get("origin", [])
    # keep searching
    for r in traits[k].requires.keys():
        todo.insert((t, r, v + [k]), 0)


# daemon ------------------------------------------------------------------------------------------


class Daemon(object):
    def __init__(self, **kwargs):
        self.protocol = kwargs["protocol"]
        self.name = self.protocol
        self.doc = kwargs["doc"]
        self.links = kwargs.get("links", dict())
        self.installation = kwargs.get("installation", dict())
        self.traits = dict()
        for t in kwargs["traits"]:
            self.traits[t] = []
            for tt in traits[t].requires:
                if tt not in self.traits.keys():
                    self.traits[tt] = [t] + traits[t].requires[tt]
        self.config = kwargs.get("config", dict())
        self.state = kwargs.get("state", dict())
        self.method = kwargs.get("method", dict())
        self.hardwares = []

    def __repr__(self):
        return self.name

    def format_origin(self, lis):
        return "from " + " ➜ ".join(
            [f"<a href='../../traits/{l}'>{l}</a>" for l in lis]
        )


daemons = {}

# initialize
for name in os.listdir(__here__ / "daemons"):
    with open(__here__ / "daemons" / name, "r") as f:
        dic = json.load(f)
    d = Daemon(**dic)
    daemons[d.name] = d

# sort
daemons = collections.OrderedDict(sorted(daemons.items()))

# back-populate
for d in daemons.values():
    for t, v in d.traits.items():
        traits[t].daemons[d.name] = v


# populate
for d in daemons.values():
    for t, v in d.traits.items():
        for c in traits[t].config.keys():
            if c not in d.config.keys():
                d.config[c] = copy.deepcopy(traits[t].config[c])
            d.config[c].update(copy.deepcopy(traits[t].config[c]))
            d.config[c]["origin"] = [t] + d.config[c].get("origin", [])
        for s in traits[t].state.keys():
            if s not in d.state.keys():
                d.state[s] = copy.deepcopy(traits[t].state[s])
                d.state[s]["origin"] = [t] + d.state[s].get("origin", [])
        for m in traits[t].method.keys():
            if m not in d.method.keys():
                d.method[m] = copy.deepcopy(traits[t].method[m])
                d.method[m]["origin"] = [t] + d.method[m].get("origin", [])


# hardware ----------------------------------------------------------------------------------------


class Hardware(object):
    def __init__(self, **kwargs):
        self.model = kwargs["model"]
        self.description = kwargs["description"]
        self.make = kwargs.get("make", None)
        self.links = kwargs.get("links", dict())
        self.daemons = kwargs["daemons"]

    def __repr__(self):
        return self.name


hardwares = {}

# initialize
for name in []:#os.listdir(__here__ / "hardware"):
    dic = toml.load(__here__ / "hardware" / name)
    h = Hardware(**dic)
    hardwares[h.model] = h
    for d in h.daemons:
        daemons[d].hardwares.append(h.model)

# sort
def key(item):
    k, v = item
    return "/".join([v.make, v.model])
hardwares = collections.OrderedDict(sorted(hardwares.items(), key=key))
