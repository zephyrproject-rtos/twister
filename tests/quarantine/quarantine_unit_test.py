
import pytest

from twister2.filter.quarantine_filter import QuarantineData
from twister2.exceptions import TwisterConfigurationException


def test_quarantine_load_data(tmp_path):
    quarantine_file = tmp_path / "quarantine.yml"
    quarantine_file.write_text("""
- scenarios:
  - test.a
  - test.b
  platforms:
    - native_posix
  comment: "comment"
- platforms:
    - qemu_x86
    """)
    qdata = QuarantineData.load_data_from_yaml(quarantine_file)
    assert len(qdata.qlist) == 2
    assert len(qdata.qlist[0].scenarios) == 2
    assert qdata.qlist[0].comment == 'comment'
    assert qdata.qlist[0].scenarios[1] == 'test.b'
    assert qdata.qlist[0].platforms[0] == 'native_posix'
    assert qdata.qlist[1].platforms[0] == 'qemu_x86'
    assert qdata.qlist[1].comment


def test_quarantine_load_data_from_two_files(tmp_path):
    quarantine_file1 = tmp_path / "quarantine1.yml"
    quarantine_file1.write_text("""
- scenarios:
  - test.a
  platforms:
    - native_posix
  comment: 'comment'
- platforms:
    - qemu_x86
    """)
    quarantine_file2 = tmp_path / "quarantine2.yml"
    quarantine_file2.write_text("""
- scenarios:
  - test.b
  architectures:
    - riscv
- architectures:
    - x86
    - arm
  comment: 'only arch filtered'
    """)
    qdata = QuarantineData()
    for qfile in [quarantine_file1, quarantine_file2]:
        qdata.extend(QuarantineData.load_data_from_yaml(qfile))
    assert len(qdata.qlist) == 4
    assert qdata.qlist[3].architectures[1] == 'arm'


def test_quarantine_raise_exception_if_data_empty(tmp_path):
    quarantine_file = tmp_path / "quarantine.yml"
    quarantine_file.write_text("""
- comment: "comment"
    """)
    with pytest.raises(TwisterConfigurationException) as err:
        QuarantineData.load_data_from_yaml(quarantine_file)
    assert err.match("At least one")
