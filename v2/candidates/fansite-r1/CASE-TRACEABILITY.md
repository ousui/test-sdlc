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


## Q1 增量追溯

源为 R0 真实交付包 d6dd4a6d16d851e35b8db34dc1444fd2dd8c3eae3466ad4a1a13c7800a6a4111。原 site_test.go 与 check_ui.py 保留字节。

R1 新增 TestR1CatalogPaginationBoundaries / TestR1StableTitleTiesAndRepeatedPages / TestR1SearchAndFilteredTotals / TestR1StrictCatalogInputsAndAuthorization / TestR1TrackStatusLifecycleAndOldMediaURL / TestR1AlbumStatusControlsDetailAndEveryPhotoURL / TestR1InvalidPublicationChangesAreAtomic / TestR1MigrateRealV1BytesAndRestartWithoutDataLoss / TestR1RestartKeepsFilteredOrderingAndWithdrawnURLs；另 ui_catalog_test.js 验证真实目录控制器交互与HTML连接。

Q1 不实施 R2 的版本冲突机制、磁盘失败专项扩展或多实例共享数据功能。
