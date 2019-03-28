#!/usr/bin/env python

def risky_matrix_remap(matrix_id, api, quiet=False):
    # take a matrix linked to a mode, assuming the first one is done properly
    #  and then try to make the others match it correctly. It is assumed that
    #  the example mode name is ONLY used for the actual mode. This will break
    #  eg. if you have modes
    #  [$PowerDrill.Drill, $PowerDrill.Repair, $PowerDrill.Off] and are trying
    #  to pattern off the mode "Drill".
    mtx = api.get_matrix(matrix_id)
    assert(len(mtx[0]) == 1)
    modes = [row[0]['shortname'] for row in mtx]
    for row, mode in zip(mtx, modes):
        formula = row[0]['formula'].replace(modes[0], mode)
        if not quiet:
            print(formula)
        api.update_vali(row[0]['id'], formula=formula)

def matrix_modes(matrix_id, formula, api):
    # the string $$mode in formula will be replaced by the appropriate mode name
    mtx = api.get_matrix(matrix_id)
    assert(len(mtx[0]) == 1)
    for row in mtx:
        this = formula.replace('$$mode', row[0]['shortname'])
        api.update_vali(row[0]['id'], formula=this)

def pc(power):
    return ('PowerConsumption', str(power), 'W')
def dc_valis(peak, duty_cycle):
    return [('MaxPowerConsumption', str(peak), 'W'),
            ('UsageRate', str(duty_cycle), ''),
            pc('$$this.MaxPowerConsumption * $$this.UsageRate')
           ]

class component:
    def __init__(self, name, valis=(), children=[], desc=None):
        self.name = name
        if len(valis):
            if type(valis[0]) is str:
                # only one vali passed
                valis = (valis,)
        self.valis = [(vali[0],
                       vali[1].replace('$$this', '$' + self.name),
                       vali[2]
                      )
                      for vali in valis]
        self.children = children
        self.desc = desc
        self.id = None
    def emit(self, api, parent_id):
        data = {'parent': parent_id, 'name': self.name}
        if self.desc is not None:
            data['description'] = self.desc
        resp = api.post('component/', data=data)
        self.id = resp['id']
        for vali in self.valis:
            data=dict(zip(('parent', 'shortname', 'formula', 'unit'),
                          (self.id,) + tuple(str(v) for v in vali)))
            api.post('vali/', data=data)
        for child in self.children:
            child.emit(api, self.id)
        return self.id
