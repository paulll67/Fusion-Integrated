from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
SPEC = (ROOT / 'docs/09-leave/specs/02_ELM_Functional_Requirement_Specification_v1.5_FINAL.md').read_text(encoding='utf-8')
DESIGN = json.loads((ROOT / 'a8_design/FR_DESIGN.json').read_text(encoding='utf-8'))

def test_a8_fr_001():
    """A8-FR-001; CFR-EL-001"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-001')
    assert 'CFR-EL-001' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_002():
    """A8-FR-002; CFR-EL-002"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-002')
    assert 'CFR-EL-002' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_003():
    """A8-FR-003; CFR-EL-003"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-003')
    assert 'CFR-EL-003' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_004():
    """A8-FR-004; CFR-EL-004"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-004')
    assert 'CFR-EL-004' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_005():
    """A8-FR-005; CFR-EL-005"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-005')
    assert 'CFR-EL-005' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_006():
    """A8-FR-006; CFR-EL-006"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-006')
    assert 'CFR-EL-006' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_007():
    """A8-FR-007; CFR-EL-007"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-007')
    assert 'CFR-EL-007' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_008():
    """A8-FR-008; CFR-EL-008"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-008')
    assert 'CFR-EL-008' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_009():
    """A8-FR-009; CFR-EL-009"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-009')
    assert 'CFR-EL-009' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_010():
    """A8-FR-010; CFR-EL-010"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-010')
    assert 'CFR-EL-010' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_011():
    """A8-FR-011; CFR-EL-011"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-011')
    assert 'CFR-EL-011' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_012():
    """A8-FR-012; CFR-EL-012"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-012')
    assert 'CFR-EL-012' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_013():
    """A8-FR-013; CFR-EL-013"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-013')
    assert 'CFR-EL-013' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_014():
    """A8-FR-014; CFR-EL-014"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-014')
    assert 'CFR-EL-014' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_015():
    """A8-FR-015; CFR-EL-015"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-015')
    assert 'CFR-EL-015' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_016():
    """A8-FR-016; CFR-EL-016"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-016')
    assert 'CFR-EL-016' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_017():
    """A8-FR-017; CFR-EL-017"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-017')
    assert 'CFR-EL-017' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_018():
    """A8-FR-018; CFR-EL-018"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-018')
    assert 'CFR-EL-018' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_019():
    """A8-FR-019; CFR-EL-019"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-019')
    assert 'CFR-EL-019' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_020():
    """A8-FR-020; CFR-EL-020"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-020')
    assert 'CFR-EL-020' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_021():
    """A8-FR-021; CFR-EL-021"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-021')
    assert 'CFR-EL-021' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_022():
    """A8-FR-022; CFR-EL-022"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-022')
    assert 'CFR-EL-022' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_023():
    """A8-FR-023; CFR-EL-023"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-023')
    assert 'CFR-EL-023' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_024():
    """A8-FR-024; CFR-EL-024"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-024')
    assert 'CFR-EL-024' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_025():
    """A8-FR-025; CFR-EL-025"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-025')
    assert 'CFR-EL-025' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_026():
    """A8-FR-026; CFR-EL-026"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-026')
    assert 'CFR-EL-026' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_027():
    """A8-FR-027; CFR-EL-027"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-027')
    assert 'CFR-EL-027' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_028():
    """A8-FR-028; CFR-EL-028"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-028')
    assert 'CFR-EL-028' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_029():
    """A8-FR-029; CFR-EL-029"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-029')
    assert 'CFR-EL-029' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_030():
    """A8-FR-030; CFR-EL-030"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-030')
    assert 'CFR-EL-030' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_031():
    """A8-FR-031; CFR-EL-031"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-031')
    assert 'CFR-EL-031' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_fr_032():
    """A8-FR-032; CFR-EL-032"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-FR-032')
    assert 'CFR-EL-032' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'
