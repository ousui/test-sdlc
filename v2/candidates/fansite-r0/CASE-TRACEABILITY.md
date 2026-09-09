# Acceptance-to-test traceability

All24 exact named tests must execute on the current terminal source; no skips or prior-run substitution.

| Acceptance | Named tests |
|---|---|
| AC-001 | TestPublicPagesAndNativeAssets |
| AC-002 | TestRegistrationProfileLoginAndLogout, TestCaseInsensitiveDuplicateAndBadInputs, TestProfileOnlyModifiesCurrentAccount |
| AC-003 | TestOrdinaryFanCannotAccessAdminOrAssignRole, TestAdministratorCannotDisableOwnManagementAccess |
| AC-004 | TestPasswordIsSaltedNotPlaintext, TestCSRFMethodOriginAndCookieFlags, TestDisableReenableCannotResurrectCookie, TestLateSessionCreationStillBindsRevocationGeneration, TestExpiredAndForgedSessionDenied |
| AC-005 | TestDraftTrackAndAlbumRemainPrivate, TestAudioGetHeadRangeAndInvalidRange, TestPublishUnpublishEditAndDeleteMusic |
| AC-006 | TestDraftTrackAndAlbumRemainPrivate, TestAlbumPhotoPublicationAndCascadeRemoval, TestDeleteSinglePhotoKeepsAlbum, TestRejectInvalidMediaAndAbsentAssociations |
| AC-007 | TestAdministratorCannotDisableOwnManagementAccess, TestPublishUnpublishEditAndDeleteMusic, TestSiteEditingEscapesHTMLAndScriptUsesTextNodes, TestCompleteFanAndAdminJourney |
| AC-008 | TestRestartPersistsEntitiesButDropsSessions, TestPersistenceFailureNeverPublishesPartialMutation, TestConcurrentDuplicateRegistrationAndContentWrites, TestCorruptStorageAndSymlinkFailClosed |
| AC-009 | TestProfileOnlyModifiesCurrentAccount, TestCSRFMethodOriginAndCookieFlags, TestStrictJSONAndBodyBudget, TestRejectInvalidMediaAndAbsentAssociations, TestSiteEditingEscapesHTMLAndScriptUsesTextNodes |
| AC-010 | TestPublicPagesAndNativeAssets, TestRestartPersistsEntitiesButDropsSessions, TestCompleteFanAndAdminJourney |

Offline build, licensed dependency hash, sample-media generation and native-JavaScript syntax are additionally checked outside formal runtime during preparation. VFY re-executes the24 named tests against its exact current source; compilation alone is not a functionality pass.


Q0 additional current checks: Go build; node --check web/app.js; Python check_ui.py for exact original-test bytes, HTML/JS form wiring, vendor/license and actual generated WAV/PNG. Current-agent self_review is separate from command evidence.
