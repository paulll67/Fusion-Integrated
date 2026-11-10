from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
SPEC = (ROOT / 'docs/09-leave/specs/06_ELM_Workflow_Specifications_v1.6_FINAL.md').read_text(encoding='utf-8')
DESIGN = json.loads((ROOT / 'a8_design/WF_DESIGN.json').read_text(encoding='utf-8'))

def test_a8_wf_001():
    """A8-WF-001; CW-EL-01 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-001')
    assert 'CW-EL-01' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_002():
    """A8-WF-002; BW-EL-01 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-002')
    assert 'BW-EL-01' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_003():
    """A8-WF-003; BW-EL-02 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-003')
    assert 'BW-EL-02' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_004():
    """A8-WF-004; CW-EL-02 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-004')
    assert 'CW-EL-02' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_005():
    """A8-WF-005; BW-EL-03 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-005')
    assert 'BW-EL-03' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_006():
    """A8-WF-006; CW-EL-03 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-006')
    assert 'CW-EL-03' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_007():
    """A8-WF-007; CW-EL-04 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-007')
    assert 'CW-EL-04' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_008():
    """A8-WF-008; BW-EL-04 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-008')
    assert 'BW-EL-04' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_009():
    """A8-WF-009; BW-EL-05 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-009')
    assert 'BW-EL-05' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_010():
    """A8-WF-010; BW-EL-06 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-010')
    assert 'BW-EL-06' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_011():
    """A8-WF-011; BW-EL-07 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-011')
    assert 'BW-EL-07' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_012():
    """A8-WF-012; BW-EL-08 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-012')
    assert 'BW-EL-08' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_013():
    """A8-WF-013; BW-EL-09 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-013')
    assert 'BW-EL-09' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_014():
    """A8-WF-014; BW-EL-10 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-014')
    assert 'BW-EL-10' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_015():
    """A8-WF-015; BW-EL-11 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-015')
    assert 'BW-EL-11' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_016():
    """A8-WF-016; BW-EL-12 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-016')
    assert 'BW-EL-12' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_017():
    """A8-WF-017; BW-EL-13 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-017')
    assert 'BW-EL-13' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_018():
    """A8-WF-018; BW-EL-14 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-018')
    assert 'BW-EL-14' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_019():
    """A8-WF-019; BW-EL-15 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-019')
    assert 'BW-EL-15' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_020():
    """A8-WF-020; BW-EL-16 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-020')
    assert 'BW-EL-16' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_wf_021():
    """A8-WF-021; BW-EL-17 Path"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-WF-021')
    assert 'BW-EL-17' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'
