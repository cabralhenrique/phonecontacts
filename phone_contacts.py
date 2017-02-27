import re
import pandas as pd

def readFile(fname):
    phone_contacts = []
    with open(fname,'r') as contacts:
        for c in contacts:
            #if len(re.findall('^FN|^TEL|^EMAIL|^ADR|^PHOTO|^NOTE',c)) :
            phone_contacts.append(c)

    phone_contacts = joinPhotoStrings(phone_contacts)

    return phone_contacts

def joinPhotoStrings(x) :
    photo = 0
    exc = []
    for p in range(len(x)):
        if re.findall('^PHOTO',x[p]):
            photo = 1
            count = []
            photo_string = ''
        elif x[p] == '\n':
            photo = -1
            x[count[0]] = photo_string
            exc = exc + count[1:]
            continue
        if photo == 1:
            count.append(p)
            photo_string = photo_string + x[p]

    x = [x[idx] for idx in range(len(x)) if not idx in exc]

    return x
def getValue(x, slt):
    if slt == 'PHOTO':
        return x.replace('PHOTO;','')
    else:
        found = re.search(':(.*)\n', x)
        if found:
            found = "".join(found.group(1).split())
            if slt == 'TEL':
                found = re.sub('[^0-9+]','',found)
                if found[:2]=='00':
                    found = '+' + found[2:]
                if not found[0] == '+' and len(found) > 10:
                    found = '+' + found
            return found
        else:
            return ''

def getSlot(x, which = 0) :
    x = x.group(1)

    # keep only last item of subplot
    x = x.split(';')[which]

    return x

def formatContacts(phone_contacts) :
    name = []
    field = []
    field_type = []
    value = []
    name0 = ''
    for c in phone_contacts:

        is_name = re.findall('^FN', c)
        if is_name:
            is_name = re.search('^FN:(.*)\n', c)
            if is_name:
                name0 = is_name.group(1)
            else:
                name0 = -1
            continue

        if name0 == -1:
            continue

        if not re.findall('^BDAY',c):
            slot = re.search('(.*);',c)
            if not slot:
                continue

            slot = getSlot(slot)
        else:
            slot = 'BDAY'

        if not slot in ['FN','TEL','EMAIL','ADR','PHOTO','BDAY']:
            continue

        # check if there's a subslot
        subslot = re.search(';(.*):',c)

        if not subslot or slot == 'PHOTO':
            if slot in ['TEL','EMAIL','ADR']:
                subslot = 'PREF'
            else:
                subslot = ''
        else:
            subslot = getSlot(subslot,-1)

        val = list(set([getValue(c, slot)]))

        name = name + [name0] * len(val)
        field = field + [slot] * len(val)
        field_type = field_type + [subslot] * len(val)
        value = value + val

    df = pd.DataFrame({
        'name': name,
        'field': field,
        'type': field_type,
        'value': value
    })

    return df

def replaceValue(x_rep, field, replace_value) :
    x_rep.replace(
        x_rep.loc[x_rep[field].isin(x0[field]), field].tolist(),
        [replace_value] * len(x.loc[x[field].isin(x0[field])])
    )

def mergeSame(x):
    for slot in ['TEL','EMAIL']:
        dupl_tel = x.loc[
            (x['field'] == slot) & (x['value'].duplicated(keep=False))
        ]['value'].unique().tolist()

        for t in dupl_tel:
            x0 = x.loc[x['value'] == t]

            name = x0.loc[x0['name'].apply(
                len) == x0['name'].apply(len).max()
            ]['name']
            x.ix[x['name'].isin(x0['name']),'name'] = name.values[0]

            if x0['type'].str.match('MAIN').sum():
                subslot = 'MAIN'
            elif x0['type'].str.match('WORK').sum():
                subslot = 'WORK'
            else:
                subslot = 'PERSONAL'

            x.ix[x['value'] == t, 'type'] = subslot

    return x.drop_duplicates()

def makeVCF(x) :

    file = open('phone_contacts.vcf','w')

    for name in x.name.unique():
        x0 = x.loc[x.name == name]

        file.write('BEGIN:VCARD\n')
        file.write('FN:%s\n' % name)
        for slot in x0.field.unique().tolist():
            if slot == 'FN':
                continue
            for subslot in x0[x0.field == slot].index.tolist():
                file.write(
                    '%s;%s:%s\n' %
                    (
                        slot,
                        x0.ix[subslot,'type'],
                        x0.ix[subslot,'value']
                    )
                )
        file.write('END:VCARD\n')

    file.close()

def organizeContacts(fnames = 0):
    if not fnames: fnames = ['my_phone.vcf','gmail.vcf']

    count = 0
    for fname in fnames:
        p_contacts = readFile(fname)

        if count:
            contacts = contacts.append(formatContacts(p_contacts))
        else:
            contacts = formatContacts(p_contacts)

        count = count + 1

    contacts = contacts.drop_duplicates()

    contacts = mergeSame(contacts)

    makeVCF(contacts)

    # return contacts

