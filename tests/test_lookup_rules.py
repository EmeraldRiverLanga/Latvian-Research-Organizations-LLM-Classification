"""Tests for the search-result rules.

Every case here comes from a mistake the pipeline actually made on live
data. A rule that was never wrong needs no test; a rule that was wrong once
will be wrong again the next time someone edits it.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lookup_rules import (host, is_directory, is_mention, is_profile,
                          name_matches, pick_description, pick_email)

MYCO = "Latvijas Mikologu biedrība"
SWANS = "Latvijas Gulbju izpētes biedrība"


# --- catalogues -----------------------------------------------------------
# Nine of ten results for a typical query are directory reflections of the
# register. Domains are endless, so the rules match on form.

@pytest.mark.parametrize("url", [
    "https://company.lursoft.lv/en/latvijas-mikologu-biedriba/40008072011",
    "https://crediweb.lv/LATVIJAS-MIKOLOGU-BIEDRIBA/40008072011",
    "https://www.euroinfopage.lv/company/mikologu/40008072011",
])
def test_registration_number_in_url_marks_a_catalogue(url):
    assert is_directory(url, host(url), MYCO)


def test_catalogue_recognised_without_being_listed():
    """balticexport and kontakti.lv were never in the domain list."""
    url = "https://balticexport.com/informacionnaja/latvijas-mikologu-biedriba"
    assert is_directory(url, host(url), MYCO)
    url = "https://latvijas-mikologu-c-24864.kontakti.lv/lv/"
    assert is_directory(url, host(url), MYCO)


def test_query_driven_database_view_is_a_catalogue():
    url = "https://blis.lps.lv/index.php?view=data&id=264&sheet_id=77"
    assert is_directory(url, host(url), MYCO)


def test_catalogue_path_needs_both_boundaries():
    """A bare '/company' would also match '/our-company-history'."""
    url = "https://example.lv/our-company-history"
    assert not is_directory(url, host(url), MYCO)


def test_an_organizations_own_site_is_not_a_catalogue():
    for url in ("https://www.folklorasbiedriba.lv/",
                "https://lab.lv/",
                "https://www.antro.lv/biedriba/"):
        assert not is_directory(url, host(url), MYCO)


# --- mentions -------------------------------------------------------------

def test_news_article_is_a_mention_not_a_home_page():
    url = ("https://www.plz.lv/baltijas-geologu-asociacija-nemiera-ar-"
           "paredzamo-zemes-dzilu-izmantosanas-regulejumu")
    assert is_mention(url, host(url))


def test_headline_slug_in_a_query_parameter_is_still_a_headline():
    """pilseta24 puts the article slug in ?slug=, not in the path."""
    url = ("https://ludza.pilseta24.lv/zina?slug=ziemelvidzemes-putnu-"
           "petniecibas-biedriba-brivpratiga-no-baltkrievijas")
    assert is_mention(url, host(url))


def test_state_institution_page_is_a_mention():
    url = "https://www.tm.gov.lv/lv/jaunums/notiks-pasakumi-par-okupaciju"
    assert is_mention(url, host(url))


def test_a_home_page_is_not_a_mention():
    url = "https://www.arheologubiedriba.lv/"
    assert not is_mention(url, host(url))


# --- platform profiles ----------------------------------------------------

def test_facebook_subpage_still_identifies_the_profile():
    """Google returned /photos/, and the strict rule rejected a real page."""
    assert is_profile("https://www.facebook.com/avpb.laterna/photos/", "facebook")


def test_facebook_group_is_not_the_organizations_profile():
    assert not is_profile(
        "https://www.facebook.com/groups/692171774191013/", "facebook")


def test_numeric_facebook_handle_is_unverifiable():
    """A handle with no words can never pass the name gate."""
    assert not is_profile("https://www.facebook.com/100082189369647/", "facebook")


def test_youtube_and_linkedin_profiles():
    assert is_profile("https://youtube.com/@lab-lv/", "youtube")
    assert is_profile("https://youtube.com/user/folklorasbiedriba", "youtube")
    assert is_profile("https://linkedin.com/company/some-society", "linkedin")
    assert not is_profile("https://linkedin.com/in/janis-berzins", "linkedin")


# --- the name gate --------------------------------------------------------

def test_short_names_require_every_distinctive_stem():
    """'Gulbju izpetes' has two stems; one match let in the natural history
    museum, whose page discussed swan research."""
    assert name_matches(SWANS, "Latvijas Gulbju izpētes biedrība sākums")
    assert not name_matches(SWANS, "Latvijas Dabas muzejs — gulbju uzskaite")


def test_case_endings_do_not_break_the_match():
    assert name_matches(MYCO, "Par Latvijas mikologu biedrību un tās darbu")


def test_a_name_with_no_distinctive_words_cannot_be_verified():
    assert not name_matches("Latvijas biedrība", "jebkāds teksts")


# --- contact extraction ---------------------------------------------------

def test_general_address_on_the_organizations_own_domain_wins():
    html = "kontakti: janis.berzins@lvea.lv un info@lvea.lv"
    assert pick_email(html, "lvea.lv") == "info@lvea.lv"


def test_technical_addresses_are_ignored():
    html = ('<img src="logo@2x.webp"> '
            '605a7bae@sentry-next.wixpress.com example@email.com '
            'info@biedriba.lv')
    assert pick_email(html, "biedriba.lv") == "info@biedriba.lv"


def test_an_address_off_the_domain_is_still_better_than_none():
    """Small associations host on Wix and keep contact on gmail."""
    html = "raksti mums: muzeologi@gmail.com"
    assert pick_email(html, "muzeologija.lv") == "muzeologi@gmail.com"


def test_no_address_returns_empty():
    assert pick_email("<html>bez kontaktiem</html>", "biedriba.lv") == ""


# --- descriptions ---------------------------------------------------------

def test_meta_description_is_used():
    html = ('<meta name="description" content="Brīvprātīga organizācija, kas '
            'apvieno praktizējošos speciālistus">')
    assert pick_description(html).startswith("Brīvprātīga organizācija")


def test_title_is_not_a_description():
    """'LFB / Sākums' is a page name; an empty field is honester."""
    assert pick_description("<title>LFB / Sākums</title>") == ""