from time import time, sleep, strftime
from shutil import copy
from epics import caget, caput
from pathlib import Path
from pyshortcuts import isotime


def instrument_current_pos(instname):
    """get current position for an instrument"""
    # print("Hello ", instname, _scandb)
    inst = _scandb.get_rows('instrument', where={'name': instname},
                         limit_one=True)
    if inst is None:
        return {}
    notes = {}
    epvs = {}
    for pvrow in _scandb.get_rows('instrument_pv', where={'instrument_id': inst.id}):
        pv = _scandb.get_rows('pv', where={'id': pvrow.pv_id}, limit_one=True)
        notes[pv.name] = pv.notes
        epvs[pv.name] = get_pv(pv.name)
    sleep(0.001)
    for name, epv in epvs.items():
        epvs[name] = (notes[name], f'{epv.get():.5f}')
    return epvs

def save_sample_images():
    _info = _scandb.get_info()
    tstamp = strftime('%b%d_%H%M%S')
    topfolder = Path(_info['server_fileroot'], _info['user_folder'])
    imgfolder = Path(topfolder, 'Sample_Images')
    micro_src = Path(_info['samplecam_micro']).as_posix()
    macro_src = Path(_info['samplecam_macro']).as_posix()
    micro_dst = Path(imgfolder, f'{tstamp}_micro.jpg')
    macro_dst = Path(imgfolder, f'{tstamp}_macro.jpg')
    copy(micro_src, micro_dst)
    copy(macro_src, macro_dst)

    micro_dst = Path(micro_dst.parent.name, micro_dst.name).as_posix()
    macro_dst = Path(macro_dst.parent.name, macro_dst.name).as_posix()
    txt = ["<hr>", "<table><tr>",
            f"    <td><a href='{micro_dst}'> <img src='{micro_dst}' width=350></a></td>"
            f"    <td><a href='{macro_dst}'> <img src='{macro_dst}' width=350></a></td>"
            "    <td><table>"]

    command = _info.get('current_command', 'unknown command')
    posname = _info.get('sample_position', None)
    if posname is None:
        eprefix = _info.get('epics_status_prefix', None)
        if eprefix is not None:
            posname_pv = get_pv(f'{eprefix}PositionName')
            time.sleep(0.001)
            if posname_pv.connected:
                posname = posname_pv.get()
    if posname is None:
        posname = 'unknown position'

    curr_pos = instrument_current_pos('SampleStage')

    # SampleStage HTML
    for desc, name, value in (('Position', posname, ''),
                              ('Command',  command, ''),
                              ('Date/Time', isotime(), ''),
                              ('Motor', 'PV Name', 'Value')):
        txt.append(f"          <tr><td>{desc}:    </td><td>{name}</td><td>{value}</td></tr>")

    for pvname, data in curr_pos.items():
        desc, value = data
        txt.append(f"          <tr><td> {desc} </td><td> {pvname} </td><td> {value}</td></tr>")
    txt.extend(["       </table></td></tr></table>", ""])
    txt = '\n'.join(txt)

    with open(Path(topfolder, 'SampleStage.html'), 'a') as fout:
        fout.write(txt)

    # Images log
    imagelog = Path(imgfolder, '_Images.tsv')
    lines = []
    if not imagelog.exists():
        lines.append('\t '.join(['DateTime', 'MicroImage', 'MacroImage', 'PositionName', 'Command']))

    lines.append('\t '.join([isotime(), micro_dst, macro_dst, posname, command]))
    with open(imagelog, 'a') as fh:
        fh.write('\n'.join(lines))
