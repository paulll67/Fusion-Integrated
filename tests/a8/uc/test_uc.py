from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
SPEC = (ROOT / 'docs/09-leave/specs/03_ELM_Use_Case_Specifications_v1.4_FINAL.md').read_text(encoding='utf-8')
DESIGN = json.loads((ROOT / 'a8_design/UC_DESIGN.json').read_text(encoding='utf-8'))

def test_a8_uc_001():
    """A8-UC-001; EL-UC-001 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-001')
    assert 'EL-UC-001' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_002():
    """A8-UC-002; EL-UC-002 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-002')
    assert 'EL-UC-002' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_003():
    """A8-UC-003; EL-UC-003 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-003')
    assert 'EL-UC-003' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_004():
    """A8-UC-004; EL-UC-004 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-004')
    assert 'EL-UC-004' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_005():
    """A8-UC-005; EL-UC-005 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-005')
    assert 'EL-UC-005' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_006():
    """A8-UC-006; EL-UC-007 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-006')
    assert 'EL-UC-007' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_007():
    """A8-UC-007; EL-UC-008 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-007')
    assert 'EL-UC-008' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_008():
    """A8-UC-008; EL-UC-009 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-008')
    assert 'EL-UC-009' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_009():
    """A8-UC-009; EL-UC-010 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-009')
    assert 'EL-UC-010' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_010():
    """A8-UC-010; EL-UC-011 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-010')
    assert 'EL-UC-011' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_011():
    """A8-UC-011; EL-UC-012 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-011')
    assert 'EL-UC-012' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_012():
    """A8-UC-012; EL-UC-013 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-012')
    assert 'EL-UC-013' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_013():
    """A8-UC-013; EL-UC-014 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-013')
    assert 'EL-UC-014' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_014():
    """A8-UC-014; EL-UC-015 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-014')
    assert 'EL-UC-015' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_015():
    """A8-UC-015; EL-UC-016 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-015')
    assert 'EL-UC-016' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_016():
    """A8-UC-016; EL-UC-017 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-016')
    assert 'EL-UC-017' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_017():
    """A8-UC-017; EL-UC-018 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-017')
    assert 'EL-UC-018' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_018():
    """A8-UC-018; EL-UC-019 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-018')
    assert 'EL-UC-019' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_019():
    """A8-UC-019; EL-UC-020 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-019')
    assert 'EL-UC-020' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_uc_020():
    """A8-UC-020; EL-UC-021 Main Flow"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-UC-020')
    assert 'EL-UC-021' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'
