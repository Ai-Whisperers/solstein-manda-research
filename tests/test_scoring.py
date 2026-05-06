"""Tests for the scoring module — composite, grades, vetoes, flags, kills."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scoring import (
    DIMS, WEIGHTS, WEIGHT_MAP,
    compute_composite, validate_dimensions,
    composite_to_grade, composite_to_readiness,
    apply_vetoes, scan_red_flags, check_kill_criteria,
)


class TestComputeComposite:
    def test_all_threes(self):
        scores = {d: 3 for d in DIMS}
        assert compute_composite(scores) == 3.0

    def test_all_fives(self):
        scores = {d: 5 for d in DIMS}
        assert compute_composite(scores) == 5.0

    def test_all_ones(self):
        scores = {d: 1 for d in DIMS}
        assert compute_composite(scores) == 1.0

    def test_weighted_sum_asymmetric(self):
        """All high-weight dims (w=3) = 5, all low-weight dims (w=1) = 1"""
        scores = {d: 3 for d in DIMS}
        for dim in ['Ownership attractiveness', 'Revenue scale fit', 'Geographic fit']:
            scores[dim] = 5
        for dim in ['Integration potential', 'Growth trajectory']:
            scores[dim] = 1
        # 5*3*3=45 + 3*2*3=18 + 1*1*2=2 = 65 / 17 = 3.8235...
        comp = compute_composite(scores)
        assert round(comp, 2) == 3.82

    def test_weighted_sum_high_ownership_low_geo(self):
        """Ownership (w=3) = 5, Geographic (w=3) = 1, rest = 3"""
        scores = {d: 3 for d in DIMS}
        scores['Ownership attractiveness'] = 5
        scores['Geographic fit'] = 1
        # (5*3=15)+(3*3=9)+(1*3=3)+(3*2*3=18)+(3*1*2=6) / 17 = 51/17 = 3.0
        # All symmetrical: the two extremes cancel out
        comp = compute_composite(scores)
        assert comp == 3.0

    def test_missing_dimension_treated_as_zero(self):
        scores = {d: 3 for d in DIMS[:4]}
        assert compute_composite(scores) < 3.0


class TestValidateDimensions:
    def test_valid_all_threes(self):
        scores = {d: 3 for d in DIMS}
        assert validate_dimensions(scores) == []

    def test_missing_dimension(self):
        scores = {d: 3 for d in DIMS if d != 'Customer lock-in'}
        errors = validate_dimensions(scores)
        assert len(errors) == 1
        assert errors[0]['dimension'] == 'Customer lock-in'
        assert errors[0]['error'] == 'missing'

    def test_out_of_range_high(self):
        scores = {d: 3 for d in DIMS}
        scores['Revenue scale fit'] = 6
        errors = validate_dimensions(scores)
        assert any(e['dimension'] == 'Revenue scale fit' and 'out of range' in e['error'] for e in errors)

    def test_out_of_range_low(self):
        scores = {d: 3 for d in DIMS}
        scores['Tech stack modernity'] = 0
        errors = validate_dimensions(scores)
        assert any(e['dimension'] == 'Tech stack modernity' and 'out of range' in e['error'] for e in errors)

    def test_invalid_type(self):
        scores = {d: 3 for d in DIMS}
        scores['Integration potential'] = 'high'
        errors = validate_dimensions(scores)
        assert any(e['dimension'] == 'Integration potential' and 'invalid type' in e['error'] for e in errors)


class TestGrades:
    def test_a_grade(self):
        grade = composite_to_grade(4.6)
        assert grade['grade'] == 'A'

    def test_b_grade(self):
        grade = composite_to_grade(4.0)
        assert grade['grade'] == 'B'

    def test_c_grade(self):
        grade = composite_to_grade(3.0)
        assert grade['grade'] == 'C'

    def test_d_grade(self):
        grade = composite_to_grade(2.0)
        assert grade['grade'] == 'D'

    def test_f_grade(self):
        grade = composite_to_grade(1.0)
        assert grade['grade'] == 'F'

    def test_none_grade(self):
        grade = composite_to_grade(None)
        assert grade['grade'] == 'N/A'

    def test_readiness_score(self):
        grade = composite_to_grade(4.0)
        assert grade['score_100'] == 80

    def test_readiness_zero(self):
        grade = composite_to_grade(0.0)
        assert grade['score_100'] == 0


class TestVetoes:
    def test_pe_owner_triggers_veto(self):
        scores = {d: 3 for d in DIMS}
        info = {'ownership': 'PE-backed by Pollen Street', 'country': 'NL', 'status': ''}
        changes = apply_vetoes(info, scores)
        assert len(changes) >= 1
        assert scores['Ownership attractiveness'] == 1

    def test_vc_backer_triggers_veto(self):
        scores = {d: 3 for d in DIMS}
        info = {'ownership': 'VC-backed, Series B from Insight', 'country': 'NL', 'status': ''}
        changes = apply_vetoes(info, scores)
        assert len(changes) >= 1

    def test_no_vc_does_not_trigger(self):
        scores = {d: 3 for d in DIMS}
        info = {'ownership': 'No VC, founder-owned', 'country': 'NL', 'status': ''}
        changes = apply_vetoes(info, scores)
        assert all(c['dimension'] != 'Ownership attractiveness' for c in changes)
        assert scores['Ownership attractiveness'] == 3

    def test_no_pe_does_not_trigger(self):
        scores = {d: 3 for d in DIMS}
        info = {'ownership': 'Private; no PE involvement', 'country': 'NL', 'status': ''}
        changes = apply_vetoes(info, scores)
        assert all(c['dimension'] != 'Ownership attractiveness' for c in changes)

    def test_us_geo_triggers_veto(self):
        scores = {d: 3 for d in DIMS}
        info = {'ownership': '', 'country': 'US', 'status': ''}
        changes = apply_vetoes(info, scores)
        assert any(c['dimension'] == 'Geographic fit' for c in changes)
        assert scores['Geographic fit'] == 1


class TestRedFlags:
    def test_no_flags_at_three(self):
        scores = {d: 3 for d in DIMS}
        assert len(scan_red_flags(scores)) == 0

    def test_critical_customer_lockin(self):
        scores = {d: 3 for d in DIMS}
        scores['Customer lock-in'] = 1
        flags = scan_red_flags(scores)
        assert any(f['name'] == 'customer_concentration' for f in flags)

    def test_warning_tech_debt(self):
        scores = {d: 3 for d in DIMS}
        scores['Tech stack modernity'] = 2
        flags = scan_red_flags(scores)
        assert any(f['name'] == 'tech_debt' for f in flags)


class TestKillCriteria:
    def test_no_kills_at_three(self):
        scores = {d: 3 for d in DIMS}
        assert len(check_kill_criteria(scores, {})) == 0

    def test_pe_owned_kill(self):
        scores = {d: 3 for d in DIMS}
        scores['Ownership attractiveness'] = 1
        kills = check_kill_criteria(scores, {'ownership': 'PE-owned by TA Associates'})
        assert any(k['name'] == 'pe_owned' for k in kills)

    def test_wrong_market_kill(self):
        scores = {d: 3 for d in DIMS}
        scores['Geographic fit'] = 1
        scores['Revenue scale fit'] = 1
        kills = check_kill_criteria(scores, {})
        assert any(k['name'] == 'wrong_market' for k in kills)

    def test_no_moat_kill(self):
        scores = {d: 3 for d in DIMS}
        scores['Customer lock-in'] = 2
        scores['Vertical depth'] = 2
        kills = check_kill_criteria(scores, {})
        assert any(k['name'] == 'no_moat' for k in kills)
