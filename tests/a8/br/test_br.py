from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
SPEC = (ROOT / 'docs/09-leave/specs/04_ELM_Business_Rule_Specifications_v1.4_FINAL.md').read_text(encoding='utf-8')
DESIGN = json.loads((ROOT / 'a8_design/BR_DESIGN.json').read_text(encoding='utf-8'))

def test_a8_br_001():
    """A8-BR-001; BR-EL-001"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-001')
    assert 'BR-EL-001' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_002():
    """A8-BR-002; BR-EL-002"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-002')
    assert 'BR-EL-002' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_003():
    """A8-BR-003; BR-EL-003"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-003')
    assert 'BR-EL-003' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_004():
    """A8-BR-004; BR-EL-004"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-004')
    assert 'BR-EL-004' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_005():
    """A8-BR-005; BR-EL-005"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-005')
    assert 'BR-EL-005' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_006():
    """A8-BR-006; BR-EL-006"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-006')
    assert 'BR-EL-006' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_007():
    """A8-BR-007; BR-EL-007"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-007')
    assert 'BR-EL-007' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_008():
    """A8-BR-008; BR-EL-008"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-008')
    assert 'BR-EL-008' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_009():
    """A8-BR-009; BR-EL-009"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-009')
    assert 'BR-EL-009' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_010():
    """A8-BR-010; BR-EL-010"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-010')
    assert 'BR-EL-010' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_011():
    """A8-BR-011; BR-EL-011"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-011')
    assert 'BR-EL-011' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_012():
    """A8-BR-012; BR-EL-012"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-012')
    assert 'BR-EL-012' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_013():
    """A8-BR-013; BR-EL-013"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-013')
    assert 'BR-EL-013' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_014():
    """A8-BR-014; BR-EL-014"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-014')
    assert 'BR-EL-014' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_015():
    """A8-BR-015; BR-EL-015"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-015')
    assert 'BR-EL-015' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_016():
    """A8-BR-016; BR-EL-016"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-016')
    assert 'BR-EL-016' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_017():
    """A8-BR-017; BR-EL-017"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-017')
    assert 'BR-EL-017' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_018():
    """A8-BR-018; BR-EL-018"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-018')
    assert 'BR-EL-018' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_019():
    """A8-BR-019; BR-EL-019"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-019')
    assert 'BR-EL-019' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_020():
    """A8-BR-020; BR-EL-020"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-020')
    assert 'BR-EL-020' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_021():
    """A8-BR-021; BR-EL-021"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-021')
    assert 'BR-EL-021' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_022():
    """A8-BR-022; BR-EL-022"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-022')
    assert 'BR-EL-022' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_023():
    """A8-BR-023; BR-EL-023"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-023')
    assert 'BR-EL-023' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_024():
    """A8-BR-024; BR-EL-024"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-024')
    assert 'BR-EL-024' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_025():
    """A8-BR-025; BR-EL-025"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-025')
    assert 'BR-EL-025' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_026():
    """A8-BR-026; BR-EL-026"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-026')
    assert 'BR-EL-026' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_027():
    """A8-BR-027; BR-EL-027"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-027')
    assert 'BR-EL-027' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_028():
    """A8-BR-028; BR-EL-028"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-028')
    assert 'BR-EL-028' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_029():
    """A8-BR-029; BR-EL-029"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-029')
    assert 'BR-EL-029' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_030():
    """A8-BR-030; BR-EL-030"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-030')
    assert 'BR-EL-030' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_031():
    """A8-BR-031; BR-EL-031"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-031')
    assert 'BR-EL-031' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_032():
    """A8-BR-032; BR-EL-032"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-032')
    assert 'BR-EL-032' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_033():
    """A8-BR-033; BR-EL-033"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-033')
    assert 'BR-EL-033' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_034():
    """A8-BR-034; BR-EL-034"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-034')
    assert 'BR-EL-034' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_035():
    """A8-BR-035; BR-EL-035"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-035')
    assert 'BR-EL-035' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_036():
    """A8-BR-036; BR-EL-036"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-036')
    assert 'BR-EL-036' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_037():
    """A8-BR-037; BR-EL-037"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-037')
    assert 'BR-EL-037' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'

def test_a8_br_038():
    """A8-BR-038; BR-EL-038"""
    case = next(item for item in DESIGN if item['test_id'] == 'A8-BR-038')
    assert 'BR-EL-038' in SPEC
    assert case['source_id'].startswith(case['source_id'].split()[0])
    assert case['test_type'] == 'backend_pytest'
