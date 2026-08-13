export interface paths {
    "/api/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_api_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_api_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/learner": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Learner Workspace */
        get: operations["get_learner_workspace_api_workspaces_learner_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/workspaces/teacher": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Teacher Workspace */
        get: operations["get_teacher_workspace_api_workspaces_teacher_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Knowledge Bases */
        get: operations["list_knowledge_bases_api_knowledge_bases_get"];
        put?: never;
        /** Create Knowledge Base */
        post: operations["create_knowledge_base_api_knowledge_bases_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Knowledge Base */
        get: operations["get_knowledge_base_api_knowledge_bases__knowledge_base_id__get"];
        put?: never;
        post?: never;
        /** Delete Knowledge Base */
        delete: operations["delete_knowledge_base_api_knowledge_bases__knowledge_base_id__delete"];
        options?: never;
        head?: never;
        /** Update Knowledge Base */
        patch: operations["update_knowledge_base_api_knowledge_bases__knowledge_base_id__patch"];
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archive Knowledge Base */
        post: operations["archive_knowledge_base_api_knowledge_bases__knowledge_base_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/copies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Copy Knowledge Base To Class */
        post: operations["copy_knowledge_base_to_class_api_knowledge_bases__knowledge_base_id__copies_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/imports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Import Knowledge Base Documents
         * @description 导入知识库文档并在服务层完成解析和索引，出错自动回滚。
         */
        post: operations["import_knowledge_base_documents_api_knowledge_bases_imports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Knowledge Base */
        post: operations["publish_knowledge_base_api_knowledge_bases__knowledge_base_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Search Knowledge Base */
        post: operations["search_knowledge_base_api_knowledge_bases__knowledge_base_id__search_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/retrieval-tests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Test Knowledge Base Retrieval */
        post: operations["test_knowledge_base_retrieval_api_knowledge_bases__knowledge_base_id__retrieval_tests_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/index-status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Knowledge Base Index Status */
        get: operations["get_knowledge_base_index_status_api_knowledge_bases__knowledge_base_id__index_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Knowledge Base Documents */
        get: operations["list_knowledge_base_documents_api_knowledge_bases__knowledge_base_id__documents_get"];
        put?: never;
        /**
         * Upload Knowledge Base Document
         * @description 上传并保存 Markdown 原文件，文档可直接进入分段预览。
         */
        post: operations["upload_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Knowledge Base Document */
        get: operations["get_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__get"];
        put?: never;
        post?: never;
        /** Delete Knowledge Base Document */
        delete: operations["delete_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__delete"];
        options?: never;
        head?: never;
        /** Update Knowledge Base Document */
        patch: operations["update_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__patch"];
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}/replace": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Replace Knowledge Base Document */
        post: operations["replace_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__replace_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Knowledge Base Settings */
        get: operations["get_knowledge_base_settings_api_knowledge_bases__knowledge_base_id__settings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Knowledge Base Settings */
        patch: operations["update_knowledge_base_settings_api_knowledge_bases__knowledge_base_id__settings_patch"];
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/segments/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Preview Knowledge Base Segments
         * @description 预览分段前确保文档已解析。
         */
        post: operations["preview_knowledge_base_segments_api_knowledge_bases__knowledge_base_id__segments_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/segments/rebuild": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Rebuild Knowledge Base Segments
         * @description 重建分段前确保文档已解析。
         */
        post: operations["rebuild_knowledge_base_segments_api_knowledge_bases__knowledge_base_id__segments_rebuild_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/{knowledge_base_id}/segments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Knowledge Base Segments */
        get: operations["list_knowledge_base_segments_api_knowledge_bases__knowledge_base_id__segments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/knowledge-bases/documents/{document_id}/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Retry Knowledge Base Document
         * @description 重试失败文档：重新解析并更新文档状态。
         */
        post: operations["retry_knowledge_base_document_api_knowledge_bases_documents__document_id__retry_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Teaching Classes
         * @description 获取教师的教学班列表
         */
        get: operations["list_teaching_classes_api_teaching_classes_get"];
        put?: never;
        /**
         * Create Teaching Class
         * @description 创建教学班
         */
        post: operations["create_teaching_class_api_teaching_classes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/join-policy": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Update Join Policy
         * @description 更新教学班加入策略
         */
        patch: operations["update_join_policy_api_teaching_classes__class_id__join_policy_patch"];
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/name": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Rename Teaching Class */
        patch: operations["rename_teaching_class_api_teaching_classes__class_id__name_patch"];
        trace?: never;
    };
    "/api/teaching-classes/{class_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Teaching Class
         * @description 根据 ID 获取教学班详情。
         */
        get: operations["get_teaching_class_api_teaching_classes__class_id__get"];
        put?: never;
        post?: never;
        /** Delete Teaching Class */
        delete: operations["delete_teaching_class_api_teaching_classes__class_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/discover": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Discover Classes
         * @description 学习者发现可加入的教学班
         */
        get: operations["discover_classes_api_teaching_classes_discover_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/mine": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Learner Classes
         * @description 获取学习者已正式加入的教学班。
         */
        get: operations["list_learner_classes_api_teaching_classes_mine_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/join": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Join Class
         * @description 学习者加入教学班
         */
        post: operations["join_class_api_teaching_classes__class_id__join_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/join-request": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Create Join Request
         * @description 学习者申请加入需要审批的教学班
         */
        post: operations["create_join_request_api_teaching_classes__class_id__join_request_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/join-requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Pending Join Requests
         * @description 教师查看待处理的加入申请
         */
        get: operations["list_pending_join_requests_api_teaching_classes__class_id__join_requests_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/join-requests/{request_id}/resolve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Resolve Join Request
         * @description 教师审批或拒绝加入申请
         */
        patch: operations["resolve_join_request_api_teaching_classes_join_requests__request_id__resolve_patch"];
        trace?: never;
    };
    "/api/teaching-classes/join-requests/mine": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Learner Join Requests
         * @description 学习者查看自己的加入申请
         */
        get: operations["list_learner_join_requests_api_teaching_classes_join_requests_mine_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/authorization-code": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Authorization Code
         * @description 获取教学班的授权码
         */
        get: operations["get_authorization_code_api_teaching_classes__class_id__authorization_code_get"];
        /**
         * Create Or Update Authorization Code
         * @description 创建或更新教学班授权码
         */
        put: operations["create_or_update_authorization_code_api_teaching_classes__class_id__authorization_code_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/join-by-authorization-code": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Join Class By Authorization Code
         * @description 通过授权码加入教学班
         */
        post: operations["join_class_by_authorization_code_api_teaching_classes_join_by_authorization_code_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/knowledge-base": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Class Knowledge Base */
        get: operations["get_class_knowledge_base_api_teaching_classes__class_id__knowledge_base_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/knowledge-base/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Search Class Knowledge Base */
        post: operations["search_class_knowledge_base_api_teaching_classes__class_id__knowledge_base_search_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/course-overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Course Overview */
        get: operations["get_course_overview_api_teaching_classes__class_id__course_overview_get"];
        /** Update Course Overview */
        put: operations["update_course_overview_api_teaching_classes__class_id__course_overview_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/course-overview/candidates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Generate Course Overview Candidates */
        post: operations["generate_course_overview_candidates_api_teaching_classes__class_id__course_overview_candidates_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Published Contents */
        get: operations["list_published_contents_api_teaching_classes__class_id__published_contents_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Published Content */
        put: operations["update_published_content_api_teaching_classes__class_id__published_contents__content_id__put"];
        post?: never;
        /** Delete Published Content */
        delete: operations["delete_published_content_api_teaching_classes__class_id__published_contents__content_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/learner": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Published Contents For Learner */
        get: operations["list_published_contents_for_learner_api_teaching_classes__class_id__published_contents_learner_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}/learner": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Published Content Detail For Learner */
        get: operations["get_published_content_detail_for_learner_api_teaching_classes__class_id__published_contents__content_id__learner_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/contents/{content_id}/complete": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Content Complete */
        post: operations["mark_content_complete_api_teaching_classes__class_id__contents__content_id__complete_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/home-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Course Home Summary */
        get: operations["get_course_home_summary_api_teaching_classes__class_id__home_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Preparation Session */
        get: operations["get_preparation_session_api_teaching_classes__class_id__preparation_session_get"];
        put?: never;
        /** Create Or Get Preparation Session */
        post: operations["create_or_get_preparation_session_api_teaching_classes__class_id__preparation_session_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Preparation Session Upload */
        put: operations["update_preparation_session_upload_api_teaching_classes__class_id__preparation_session_upload_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/parse": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Preparation Session Parsing */
        post: operations["start_preparation_session_parsing_api_teaching_classes__class_id__preparation_session_parse_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Preparation Session Parsed Paragraphs */
        get: operations["get_preparation_session_parsed_paragraphs_api_teaching_classes__class_id__preparation_session_parsed_paragraphs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Preparation Session Parsed Paragraphs With Highlights */
        get: operations["get_preparation_session_parsed_paragraphs_with_highlights_api_teaching_classes__class_id__preparation_session_parsed_paragraphs_with_highlights_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/highlights": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Highlight */
        post: operations["add_highlight_api_teaching_classes__class_id__preparation_session_highlights_post"];
        /** Remove Highlight */
        delete: operations["remove_highlight_api_teaching_classes__class_id__preparation_session_highlights_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/questions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Questions */
        get: operations["list_questions_api_teaching_classes__class_id__preparation_session_questions_get"];
        put?: never;
        /** Create Question */
        post: operations["create_question_api_teaching_classes__class_id__preparation_session_questions_post"];
        /** Delete Question */
        delete: operations["delete_question_api_teaching_classes__class_id__preparation_session_questions_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/questions/{question_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Question */
        put: operations["update_question_api_teaching_classes__class_id__preparation_session_questions__question_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/questions/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Candidate Question */
        post: operations["confirm_candidate_question_api_teaching_classes__class_id__preparation_session_questions_confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/questions/candidates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Generate Candidate Questions */
        post: operations["generate_candidate_questions_api_teaching_classes__class_id__preparation_session_questions_candidates_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/questions/{question_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Preparation Question */
        post: operations["publish_preparation_question_api_teaching_classes__class_id__preparation_session_questions__question_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Preparation Session */
        post: operations["publish_preparation_session_api_teaching_classes__class_id__preparation_session_publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/publish-homework": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Homework */
        post: operations["publish_homework_api_teaching_classes__class_id__preparation_session_publish_homework_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/preparation-session/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Select Preparation Session Documents */
        post: operations["select_preparation_session_documents_api_teaching_classes__class_id__preparation_session_documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}/practice-detail": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Classroom Practice Content Detail */
        get: operations["get_classroom_practice_content_detail_api_teaching_classes__class_id__published_contents__content_id__practice_detail_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Classroom Practice Answer */
        post: operations["submit_classroom_practice_answer_api_teaching_classes__class_id__published_contents__content_id__submit_answer_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Baseline Practice Detail */
        get: operations["get_baseline_practice_detail_api_teaching_classes__class_id__published_contents__content_id__baseline_practice_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Baseline Practice Answer */
        post: operations["submit_baseline_practice_answer_api_teaching_classes__class_id__published_contents__content_id__baseline_practice_submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice/abandon": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Abandon Baseline Practice */
        post: operations["abandon_baseline_practice_api_teaching_classes__class_id__published_contents__content_id__baseline_practice_abandon_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/mastery-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Mastery Summary */
        get: operations["get_mastery_summary_api_teaching_classes__class_id__mastery_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/homework/{homework_id}/save-draft": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Save Homework Draft */
        post: operations["save_homework_draft_api_teaching_classes__class_id__homework__homework_id__save_draft_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/homework/{homework_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Homework */
        post: operations["submit_homework_api_teaching_classes__class_id__homework__homework_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/homework/{homework_id}/submission": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Homework Submission Detail */
        get: operations["get_homework_submission_detail_api_teaching_classes__class_id__homework__homework_id__submission_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/homework": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Homework For Learner */
        get: operations["list_homework_for_learner_api_teaching_classes__class_id__homework_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/teacher-homework": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Teacher Homework */
        get: operations["list_teacher_homework_api_teaching_classes__class_id__teacher_homework_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/pairing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Webots Pairing */
        post: operations["create_webots_pairing_api_teaching_classes__class_id__webots_pairing_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/pairing/bind": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Bind Webots Pairing */
        post: operations["bind_webots_pairing_api_teaching_classes__class_id__webots_pairing_bind_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/environment": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Report Webots Environment */
        post: operations["report_webots_environment_api_teaching_classes__class_id__webots_environment_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/environment/{connector_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Webots Environment */
        get: operations["get_webots_environment_api_teaching_classes__class_id__webots_environment__connector_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/tasks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Webots Tasks */
        get: operations["list_webots_tasks_api_teaching_classes__class_id__webots_tasks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Webots Runs */
        get: operations["list_webots_runs_api_teaching_classes__class_id__webots_runs_get"];
        put?: never;
        /** Create Webots Run */
        post: operations["create_webots_run_api_teaching_classes__class_id__webots_runs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/runs/{run_id}/command": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Command Webots Run */
        post: operations["command_webots_run_api_teaching_classes__class_id__webots_runs__run_id__command_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/runs/{run_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Webots Event */
        post: operations["add_webots_event_api_teaching_classes__class_id__webots_runs__run_id__events_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/runs/{run_id}/result": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Webots Result */
        post: operations["submit_webots_result_api_teaching_classes__class_id__webots_runs__run_id__result_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Validate Webots Envelope */
        post: operations["validate_webots_envelope_api_teaching_classes__class_id__webots_messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/aggregate-stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Class Aggregate Stats */
        get: operations["get_class_aggregate_stats_api_teaching_classes__class_id__aggregate_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/teacher-dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Teacher Dashboard */
        get: operations["get_teacher_dashboard_api_teaching_classes__class_id__teacher_dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/teacher-dashboard/ai-analysis": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Generate Teacher Ai Analysis
         * @description 小 B：只把当前教师自有班级的聚合事实发送给模型。
         */
        post: operations["generate_teacher_ai_analysis_api_teaching_classes__class_id__teacher_dashboard_ai_analysis_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/webots/simulation-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Teacher Simulation Summary */
        get: operations["get_teacher_simulation_summary_api_teaching_classes__class_id__webots_simulation_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/learners": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Class Learners */
        get: operations["get_class_learners_api_teaching_classes__class_id__learners_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/learners/{learner_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Learner Detail */
        get: operations["get_learner_detail_api_teaching_classes__class_id__learners__learner_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/learners/{learner_id}/webots/simulation-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Teacher Learner Simulation Summary */
        get: operations["get_teacher_learner_simulation_summary_api_teaching_classes__class_id__learners__learner_id__webots_simulation_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/teaching-classes/{class_id}/homework/{homework_id}/ai-analysis/{learner_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Homework Ai Analysis
         * @description 小C：AI 作业批改分析 - 对指定学习者的已提交作业生成错因分析与学习建议。
         */
        get: operations["get_homework_ai_analysis_api_teaching_classes__class_id__homework__homework_id__ai_analysis__learner_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/xiaod/chat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Ask Xiaod */
        post: operations["ask_xiaod_api_xiaod_chat_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /**
         * AddHighlightRequest
         * @description 新增教学重点请求
         */
        AddHighlightRequest: {
            /** Paragraphordinal */
            paragraphOrdinal: number;
            /** Startoffset */
            startOffset: number;
            /** Endoffset */
            endOffset: number;
        };
        /** ApiResponse[AuthPayload] */
        ApiResponse_AuthPayload_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["AuthPayload"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[AuthorizationCodeView] */
        ApiResponse_AuthorizationCodeView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["AuthorizationCodeView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[BaselinePracticeDetail] */
        ApiResponse_BaselinePracticeDetail_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["BaselinePracticeDetail"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[BaselinePracticeResult] */
        ApiResponse_BaselinePracticeResult_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["BaselinePracticeResult"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[CandidateQuestionGenerationView] */
        ApiResponse_CandidateQuestionGenerationView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["CandidateQuestionGenerationView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[ClassAggregateStatsView] */
        ApiResponse_ClassAggregateStatsView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["ClassAggregateStatsView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[ClassroomPracticeContentDetailView] */
        ApiResponse_ClassroomPracticeContentDetailView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["ClassroomPracticeContentDetailView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[ClassroomPracticeResultView] */
        ApiResponse_ClassroomPracticeResultView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["ClassroomPracticeResultView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[ConnectorView] */
        ApiResponse_ConnectorView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["ConnectorView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[CourseContentCompletionView] */
        ApiResponse_CourseContentCompletionView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["CourseContentCompletionView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[CourseHomeSummaryView] */
        ApiResponse_CourseHomeSummaryView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["CourseHomeSummaryView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[CourseOverviewCandidateView] */
        ApiResponse_CourseOverviewCandidateView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["CourseOverviewCandidateView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[CourseOverview] */
        ApiResponse_CourseOverview_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["CourseOverview"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[CreateJoinRequestResponse] */
        ApiResponse_CreateJoinRequestResponse_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["CreateJoinRequestResponse"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[DiscoverableClassListView] */
        ApiResponse_DiscoverableClassListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["DiscoverableClassListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[EnvironmentView] */
        ApiResponse_EnvironmentView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["EnvironmentView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[HighlightView] */
        ApiResponse_HighlightView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["HighlightView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[HomeworkAIAnalysisView] */
        ApiResponse_HomeworkAIAnalysisView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["HomeworkAIAnalysisView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[HomeworkListView] */
        ApiResponse_HomeworkListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["HomeworkListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[HomeworkSubmissionDetailView] */
        ApiResponse_HomeworkSubmissionDetailView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["HomeworkSubmissionDetailView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[HomeworkSubmissionResultView] */
        ApiResponse_HomeworkSubmissionResultView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["HomeworkSubmissionResultView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[HomeworkSubmissionView] */
        ApiResponse_HomeworkSubmissionView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["HomeworkSubmissionView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[JoinClassResponse] */
        ApiResponse_JoinClassResponse_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["JoinClassResponse"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[JoinRequestListView] */
        ApiResponse_JoinRequestListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["JoinRequestListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseDocumentListView] */
        ApiResponse_KnowledgeBaseDocumentListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseDocumentListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseDocumentView] */
        ApiResponse_KnowledgeBaseDocumentView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseDocumentView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseImportView] */
        ApiResponse_KnowledgeBaseImportView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseImportView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseIndexStatusView] */
        ApiResponse_KnowledgeBaseIndexStatusView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseIndexStatusView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseListView] */
        ApiResponse_KnowledgeBaseListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBasePublicationView] */
        ApiResponse_KnowledgeBasePublicationView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBasePublicationView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseSearchView] */
        ApiResponse_KnowledgeBaseSearchView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseSearchView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseSegmentListView] */
        ApiResponse_KnowledgeBaseSegmentListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseSegmentListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseSegmentPreviewView] */
        ApiResponse_KnowledgeBaseSegmentPreviewView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseSegmentPreviewView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseSegmentRebuildView] */
        ApiResponse_KnowledgeBaseSegmentRebuildView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseSegmentRebuildView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseSettingsView] */
        ApiResponse_KnowledgeBaseSettingsView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseSettingsView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[KnowledgeBaseView] */
        ApiResponse_KnowledgeBaseView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[LearnerClassListView] */
        ApiResponse_LearnerClassListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["LearnerClassListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[LearnerDetailView] */
        ApiResponse_LearnerDetailView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["LearnerDetailView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[LearnerListView] */
        ApiResponse_LearnerListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["LearnerListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[MasterySummaryView] */
        ApiResponse_MasterySummaryView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["MasterySummaryView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[NoneType] */
        ApiResponse_NoneType_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            /** Data */
            data: null;
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PairingView] */
        ApiResponse_PairingView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PairingView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PreparationSessionParsingResultView] */
        ApiResponse_PreparationSessionParsingResultView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PreparationSessionParsingResultView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PreparationSessionParsingResultWithHighlightsView] */
        ApiResponse_PreparationSessionParsingResultWithHighlightsView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PreparationSessionParsingResultWithHighlightsView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PreparationSessionView] */
        ApiResponse_PreparationSessionView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PreparationSessionView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[ProtocolEnvelope] */
        ApiResponse_ProtocolEnvelope_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["ProtocolEnvelope"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PublishHomeworkResponse] */
        ApiResponse_PublishHomeworkResponse_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PublishHomeworkResponse"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PublishedContentDetailView] */
        ApiResponse_PublishedContentDetailView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PublishedContentDetailView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[PublishedContentListView] */
        ApiResponse_PublishedContentListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["PublishedContentListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[QuestionListView] */
        ApiResponse_QuestionListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["QuestionListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[QuestionPublicationView] */
        ApiResponse_QuestionPublicationView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["QuestionPublicationView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[QuestionView] */
        ApiResponse_QuestionView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["QuestionView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[ResolveJoinRequestResponse] */
        ApiResponse_ResolveJoinRequestResponse_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["ResolveJoinRequestResponse"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[RunView] */
        ApiResponse_RunView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["RunView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[SimulationSummaryView] */
        ApiResponse_SimulationSummaryView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["SimulationSummaryView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TaskCatalogView] */
        ApiResponse_TaskCatalogView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TaskCatalogView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeacherAIAnalysisView] */
        ApiResponse_TeacherAIAnalysisView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeacherAIAnalysisView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeacherDashboardView] */
        ApiResponse_TeacherDashboardView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeacherDashboardView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeacherHomeworkListView] */
        ApiResponse_TeacherHomeworkListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeacherHomeworkListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeacherPublishedContentListView] */
        ApiResponse_TeacherPublishedContentListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeacherPublishedContentListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeacherPublishedContentView] */
        ApiResponse_TeacherPublishedContentView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeacherPublishedContentView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeachingClassListView] */
        ApiResponse_TeachingClassListView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeachingClassListView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[TeachingClassView] */
        ApiResponse_TeachingClassView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["TeachingClassView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[Union[AuthorizationCodeView, NoneType]] */
        ApiResponse_Union_AuthorizationCodeView__NoneType__: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["AuthorizationCodeView"] | null;
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[Union[KnowledgeBaseWorkspaceView, NoneType]] */
        ApiResponse_Union_KnowledgeBaseWorkspaceView__NoneType__: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["KnowledgeBaseWorkspaceView"] | null;
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[UserView] */
        ApiResponse_UserView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["UserView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[WorkspaceView] */
        ApiResponse_WorkspaceView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["WorkspaceView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[XiaodChatView] */
        ApiResponse_XiaodChatView_: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            data: components["schemas"]["XiaodChatView"];
            /** Requestid */
            requestId: string;
        };
        /** ApiResponse[list[RunView]] */
        ApiResponse_list_RunView__: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            /** Data */
            data: components["schemas"]["RunView"][];
            /** Requestid */
            requestId: string;
        };
        /** AuthPayload */
        AuthPayload: {
            user: components["schemas"]["UserView"];
            /** Accesstoken */
            accessToken: string;
        };
        /**
         * AuthorizationCodeView
         * @description 班级授权码视图
         */
        AuthorizationCodeView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            /** Code */
            code: string;
            /** Enabled */
            enabled: boolean;
            /** Expiresat */
            expiresAt: number | null;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
        };
        /**
         * BaselinePracticeDetail
         * @description 基准练习详情
         */
        BaselinePracticeDetail: {
            /** Learnerid */
            learnerId: string;
            /** Classid */
            classId: string;
            /** Contentid */
            contentId: string;
            status: components["schemas"]["BaselinePracticeStatus"];
            /** Firstattemptanswers */
            firstAttemptAnswers?: number[];
            /** Secondattemptanswers */
            secondAttemptAnswers?: number[];
            /** Finalanswers */
            finalAnswers?: number[];
            /** Iscorrect */
            isCorrect?: boolean | null;
            /** Correctanswers */
            correctAnswers?: number[];
            /**
             * Hint
             * @default
             */
            hint: string;
            /**
             * Explanation
             * @default
             */
            explanation: string;
            /** Missedselections */
            missedSelections?: number[];
            /** Wrongselections */
            wrongSelections?: number[];
            /** Questiontype */
            questionType: string;
            /**
             * Difficulty
             * @default
             */
            difficulty: string;
            /** Knowledgepoints */
            knowledgePoints?: string[];
            /**
             * Source
             * @default
             */
            source: string;
            /**
             * Score
             * @default 0
             */
            score: number;
            resultType?: components["schemas"]["ResultType"] | null;
            /**
             * Attemptquality
             * @default 0
             */
            attemptQuality: number;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
        };
        /**
         * BaselinePracticeResult
         * @description 基准练习提交结果
         */
        BaselinePracticeResult: {
            /** Iscorrect */
            isCorrect: boolean;
            status: components["schemas"]["BaselinePracticeStatus"];
            /** Correctanswers */
            correctAnswers?: number[];
            /**
             * Explanation
             * @default
             */
            explanation: string;
            /**
             * Hint
             * @default
             */
            hint: string;
            /**
             * Cansubmitagain
             * @default true
             */
            canSubmitAgain: boolean;
        };
        /**
         * BaselinePracticeStatus
         * @description 基准练习状态
         * @enum {string}
         */
        BaselinePracticeStatus: "initial" | "prompt_shown" | "completed" | "abandoned";
        /**
         * BaselinePracticeSubmitRequest
         * @description 基准练习 HTTP 提交请求；学习者身份由当前会话提供。
         */
        BaselinePracticeSubmitRequest: {
            /** Selectedanswers */
            selectedAnswers?: number[];
        };
        /** Body_replace_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__replace_post */
        Body_replace_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__replace_post: {
            /**
             * File
             * Format: binary
             */
            file: Blob;
        };
        /** Body_update_preparation_session_upload_api_teaching_classes__class_id__preparation_session_upload_put */
        Body_update_preparation_session_upload_api_teaching_classes__class_id__preparation_session_upload_put: {
            /**
             * File
             * Format: binary
             */
            file: Blob;
        };
        /** Body_upload_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents_post */
        Body_upload_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents_post: {
            /**
             * File
             * Format: binary
             */
            file: Blob;
        };
        /**
         * CandidateQuestionGenerationRequest
         * @description 根据选中的教学重点生成指定数量的单选候选题。
         */
        CandidateQuestionGenerationRequest: {
            /** Highlightids */
            highlightIds: string[];
            /** Questioncount */
            questionCount: number;
        };
        /**
         * CandidateQuestionGenerationView
         * @description 小A候选题生成结果；候选仍需教师审核后才能发布。
         */
        CandidateQuestionGenerationView: {
            /** Items */
            items: components["schemas"]["QuestionView"][];
            /**
             * Status
             * @enum {string}
             */
            status: "success" | "degraded";
            /**
             * Source
             * @enum {string}
             */
            source: "integrated" | "demo" | "unconfigured" | "degraded";
            /** Message */
            message: string;
        };
        /**
         * ClassAggregateStatsView
         * @description 班级聚合统计视图
         */
        ClassAggregateStatsView: {
            /**
             * Status
             * @description 响应状态
             * @default success
             */
            status: string;
            /**
             * Message
             * @description 响应消息
             * @default
             */
            message: string;
            /**
             * Totalmembers
             * @description 班级正式成员总数
             * @default 0
             */
            totalMembers: number;
            /**
             * Contentcompletionrate
             * @description 课件平均完成率（0-1）
             * @default 0
             */
            contentCompletionRate: number;
            /**
             * Atleastonecompleted
             * @description 至少完成一项内容的人数
             * @default 0
             */
            atLeastOneCompleted: number;
            /** @description 掌握度分布 */
            masteryDistribution?: components["schemas"]["MasteryDistributionView"] | null;
            /**
             * Simulationstatus
             * @description Webots 尚无真实实训事实
             * @default no_data
             * @constant
             */
            simulationStatus: "no_data";
            /**
             * Insufficientsample
             * @description 样本不足标记
             * @default false
             */
            insufficientSample: boolean;
            /**
             * Nodata
             * @description 无数据标记
             * @default false
             */
            noData: boolean;
        };
        /**
         * ClassroomPracticeAnswerBody
         * @description 课堂练习作答 HTTP 请求体；class_id/content_id 以路径参数为唯一来源
         */
        ClassroomPracticeAnswerBody: {
            /** Selectedanswers */
            selectedAnswers: number[];
        };
        /**
         * ClassroomPracticeAttemptView
         * @description 课堂练习作答记录视图
         */
        ClassroomPracticeAttemptView: {
            /** Id */
            id: string;
            /** Learnerid */
            learnerId: string;
            /** Classid */
            classId: string;
            /** Contentid */
            contentId: string;
            /** Selectedanswers */
            selectedAnswers: number[];
            /** Iscorrect */
            isCorrect: boolean;
            /** Attemptedat */
            attemptedAt: number;
            /** Createdat */
            createdAt: number;
        };
        /**
         * ClassroomPracticeContentDetailView
         * @description 课堂练习内容详情视图，包含题目信息和作答状态
         */
        ClassroomPracticeContentDetailView: {
            content: components["schemas"]["PublishedContentDetailView"];
            attempt?: components["schemas"]["ClassroomPracticeAttemptView"] | null;
            /**
             * Cansubmit
             * @default true
             */
            canSubmit: boolean;
            /** Correctanswers */
            correctAnswers?: number[];
            /**
             * Explanation
             * @default
             */
            explanation: string;
        };
        /**
         * ClassroomPracticeResultView
         * @description 课堂练习核对结果视图
         */
        ClassroomPracticeResultView: {
            /** Iscorrect */
            isCorrect: boolean;
            /** Correctanswers */
            correctAnswers: number[];
            /**
             * Explanation
             * @default
             */
            explanation: string;
            attempt?: components["schemas"]["ClassroomPracticeAttemptView"] | null;
        };
        /**
         * ConfirmCandidateQuestionRequest
         * @description 确认候选题请求
         */
        ConfirmCandidateQuestionRequest: {
            /** Questionid */
            questionId: string;
        };
        /** ConnectorView */
        ConnectorView: {
            /** Connectorid */
            connectorId: string;
            /** Connectortoken */
            connectorToken: string;
            /** Classid */
            classId: string;
            /** Learnerid */
            learnerId: string;
            /**
             * Source
             * @default demo
             * @constant
             */
            source: "demo";
            /** Boundat */
            boundAt: number;
        };
        /**
         * ContentType
         * @description 内容类型
         * @enum {string}
         */
        ContentType: "knowledge_point" | "knowledge_module" | "teaching_resource" | "question" | "competency_objective" | "homework";
        /** CopyKnowledgeBaseRequest */
        CopyKnowledgeBaseRequest: {
            /** Targetclassid */
            targetClassId: string;
            /** Name */
            name?: string | null;
        };
        /**
         * CourseCompletionStatsView
         * @description 课程完成统计；所有完成率统一使用 0-1 比率。
         */
        CourseCompletionStatsView: {
            /**
             * Totalcontents
             * @default 0
             */
            totalContents: number;
            /**
             * Completedcontents
             * @default 0
             */
            completedContents: number;
            /**
             * Completionrate
             * @description 个人完成率（0-1）
             * @default 0
             */
            completionRate: number;
        };
        /**
         * CourseContentCompletionView
         * @description 课程内容完成记录视图
         */
        CourseContentCompletionView: {
            /** Id */
            id: string;
            /** Learnerid */
            learnerId: string;
            /** Classid */
            classId: string;
            /** Contentid */
            contentId: string;
            /** Completedat */
            completedAt: number;
            /** Createdat */
            createdAt: number;
        };
        /**
         * CourseHomeSummaryView
         * @description 课程首页汇总视图
         */
        CourseHomeSummaryView: {
            nextContent?: components["schemas"]["PublishedContentView"] | null;
            /** Contentlist */
            contentList?: components["schemas"]["PublishedContentView"][];
            completionStats?: components["schemas"]["CourseCompletionStatsView"];
            /** Pendinghomework */
            pendingHomework?: components["schemas"]["PublishedContentView"][];
            /** Nextsuggestions */
            nextSuggestions?: string[];
            masterySummary?: components["schemas"]["MasterySummaryView"];
        };
        /**
         * CourseOverview
         * @description 课程概述
         */
        CourseOverview: {
            /** Knowledgepoints */
            knowledgePoints: number;
            /** Knowledgemodules */
            knowledgeModules: number;
            /** Teachingresources */
            teachingResources: number;
            /** Questions */
            questions: number;
            /** Competencyobjectives */
            competencyObjectives: number;
            /** Background */
            background: string;
            /** Introduction */
            introduction: string;
            /** Objectives */
            objectives: string;
            /** Features */
            features: string;
        };
        /**
         * CourseOverviewCandidateView
         * @description 课程概述候选内容；候选必须由教师显式采用后才保存。
         */
        CourseOverviewCandidateView: {
            /** Background */
            background: string;
            /** Introduction */
            introduction: string;
            /** Objectives */
            objectives: string;
            /** Features */
            features: string;
            /**
             * Status
             * @enum {string}
             */
            status: "success" | "degraded";
            /**
             * Source
             * @enum {string}
             */
            source: "integrated" | "demo" | "unconfigured" | "degraded";
            /** Message */
            message: string;
        };
        /**
         * CreateJoinRequestResponse
         * @description 创建加入申请响应
         */
        CreateJoinRequestResponse: {
            /** Requestid */
            requestId: string;
            /** Classid */
            classId: string;
            /** Learnerid */
            learnerId: string;
            status: components["schemas"]["JoinRequestStatus"];
            /** Createdat */
            createdAt: number;
            /** Isnewrequest */
            isNewRequest: boolean;
        };
        /** CreateKnowledgeBaseRequest */
        CreateKnowledgeBaseRequest: {
            /** Name */
            name: string;
            /**
             * Description
             * @default
             */
            description: string;
        };
        /**
         * CreateOrUpdateAuthorizationCodeRequest
         * @description 创建或更新授权码请求
         */
        CreateOrUpdateAuthorizationCodeRequest: {
            /**
             * Enabled
             * @default true
             */
            enabled: boolean;
            /** Expiresat */
            expiresAt?: number | null;
        };
        /**
         * CreateQuestionRequest
         * @description 创建题目请求
         */
        CreateQuestionRequest: {
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /** Answers */
            answers: number[];
            /** Knowledgepoints */
            knowledgePoints: string[];
            /** Highlightsourceids */
            highlightSourceIds: string[];
            /**
             * Hint
             * @default
             */
            hint: string;
            /**
             * Explanation
             * @default
             */
            explanation: string;
        };
        /**
         * CreateTeachingClassRequest
         * @description 创建教学班请求
         */
        CreateTeachingClassRequest: {
            /** Name */
            name: string;
            joinPolicy: components["schemas"]["JoinPolicy"];
        };
        /**
         * CurrentStep
         * @description 当前步骤
         * @enum {string}
         */
        CurrentStep: "upload" | "parsing" | "highlighting" | "questioning" | "publishing";
        /**
         * DeleteQuestionRequest
         * @description 删除题目请求
         */
        DeleteQuestionRequest: {
            /** Questionid */
            questionId: string;
        };
        /**
         * DiscoverableClassListView
         * @description 可发现教学班列表视图
         */
        DiscoverableClassListView: {
            /** Items */
            items: components["schemas"]["DiscoverableClassView"][];
        };
        /**
         * DiscoverableClassView
         * @description 可发现教学班视图（学习者视角）
         */
        DiscoverableClassView: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            joinPolicy: components["schemas"]["JoinPolicy"];
            /** Membercount */
            memberCount: number;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /**
             * Ismember
             * @default false
             */
            isMember: boolean;
        };
        /** EnvironmentReportRequest */
        EnvironmentReportRequest: {
            /** Connectorid */
            connectorId: string;
            /** Environment */
            environment?: {
                [key: string]: string;
            };
        };
        /** EnvironmentView */
        EnvironmentView: {
            /** Connectorid */
            connectorId: string;
            /** Environment */
            environment: {
                [key: string]: string;
            };
            /**
             * Source
             * @default demo
             * @constant
             */
            source: "demo";
            /** Reportedat */
            reportedAt: number;
        };
        /**
         * FileFormat
         * @description 文件格式
         * @enum {string}
         */
        FileFormat: "pdf" | "docx" | "markdown";
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /**
         * HighlightView
         * @description 教学重点视图
         */
        HighlightView: {
            /** Id */
            id: string;
            /** Paragraphordinal */
            paragraphOrdinal: number;
            /** Startoffset */
            startOffset: number;
            /** Endoffset */
            endOffset: number;
            /** Createdat */
            createdAt: number;
        };
        /**
         * HomeworkAIAnalysisView
         * @description AI 作业分析响应。
         */
        HomeworkAIAnalysisView: {
            /** Homeworkid */
            homeworkId: string;
            /** Learnerid */
            learnerId: string;
            /**
             * Analysis
             * @description AI 作业整体分析（含知识点掌握情况和常见问题）
             */
            analysis: string | null;
            /**
             * Suggestions
             * @description AI 学习建议列表
             */
            suggestions?: string[];
            /**
             * Source
             * @description 来源状态：integrated / demo / unconfigured / degraded
             */
            source: string;
        };
        /**
         * HomeworkListView
         * @description 作业列表视图
         */
        HomeworkListView: {
            /** Items */
            items: components["schemas"]["PublishedContentView"][];
            /** Submissions */
            submissions?: {
                [key: string]: components["schemas"]["HomeworkSubmissionView"];
            };
        };
        /**
         * HomeworkQuestionPreviewView
         * @description 作业题目预览视图（提交前），不包含答案信息
         */
        HomeworkQuestionPreviewView: {
            /** Id */
            id: string;
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /**
             * Hint
             * @default
             */
            hint: string;
        };
        /**
         * HomeworkQuestionResultView
         * @description 作业题目结果视图（提交后），包含判分详情
         */
        HomeworkQuestionResultView: {
            /** Id */
            id: string;
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /**
             * Hint
             * @default
             */
            hint: string;
            /** Useranswers */
            userAnswers: number[];
            /** Correctanswers */
            correctAnswers: number[];
            /** Iscorrect */
            isCorrect: boolean;
            /** Score */
            score: number;
            /**
             * Explanation
             * @default
             */
            explanation: string;
        };
        /**
         * HomeworkSubmissionDetailView
         * @description 作业提交详情视图，包含作业内容和判分详情
         */
        HomeworkSubmissionDetailView: {
            submission?: components["schemas"]["HomeworkSubmissionView"] | null;
            homework: components["schemas"]["PublishedContentView"];
            /** Questions */
            questions?: (components["schemas"]["HomeworkQuestionPreviewView"] | components["schemas"]["HomeworkQuestionResultView"])[];
        };
        /**
         * HomeworkSubmissionResultView
         * @description 作业提交结果视图
         */
        HomeworkSubmissionResultView: {
            submission: components["schemas"]["HomeworkSubmissionView"];
            homework: components["schemas"]["PublishedContentView"];
            /** Questions */
            questions?: components["schemas"]["HomeworkQuestionResultView"][];
        };
        /**
         * HomeworkSubmissionStatus
         * @description 作业提交状态
         * @enum {string}
         */
        HomeworkSubmissionStatus: "draft" | "submitted";
        /**
         * HomeworkSubmissionView
         * @description 作业提交视图
         */
        HomeworkSubmissionView: {
            /** Id */
            id: string;
            /** Learnerid */
            learnerId: string;
            /** Classid */
            classId: string;
            /** Homeworkid */
            homeworkId: string;
            status: components["schemas"]["HomeworkSubmissionStatus"];
            /**
             * Answersjson
             * @default {}
             */
            answersJson: string;
            /**
             * Gradingjson
             * @default {}
             */
            gradingJson: string;
            /**
             * Totalscore
             * @default 0
             */
            totalScore: number;
            /**
             * Correctcount
             * @default 0
             */
            correctCount: number;
            /** Draftsavedat */
            draftSavedAt?: number | null;
            /** Submittedat */
            submittedAt?: number | null;
            /**
             * Islatesubmission
             * @default false
             */
            isLateSubmission: boolean;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
        };
        /** ImportKnowledgeBaseDocumentsRequest */
        ImportKnowledgeBaseDocumentsRequest: {
            /** Targetclassid */
            targetClassId: string;
            /** Items */
            items: components["schemas"]["KnowledgeBaseImportItem"][];
            /**
             * Conflictstrategy
             * @default skip
             * @enum {string}
             */
            conflictStrategy: "skip" | "replace" | "copy";
        };
        /**
         * JoinByAuthorizationCodeRequest
         * @description 通过授权码加入班级请求
         */
        JoinByAuthorizationCodeRequest: {
            /** Code */
            code: string;
        };
        /**
         * JoinClassResponse
         * @description 加入班级响应
         */
        JoinClassResponse: {
            /** Classid */
            classId: string;
            /** Learnerid */
            learnerId: string;
            /** Joinedat */
            joinedAt: number;
            /** Isnewmember */
            isNewMember: boolean;
        };
        /**
         * JoinPolicy
         * @description 教学班加入策略
         * @enum {string}
         */
        JoinPolicy: "free" | "approval" | "closed";
        /**
         * JoinRequestListView
         * @description 加入申请列表视图
         */
        JoinRequestListView: {
            /** Items */
            items: components["schemas"]["JoinRequestView"][];
        };
        /**
         * JoinRequestStatus
         * @description 加入申请状态
         * @enum {string}
         */
        JoinRequestStatus: "pending" | "approved" | "rejected";
        /**
         * JoinRequestView
         * @description 加入申请视图
         */
        JoinRequestView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            /** Learnerid */
            learnerId: string;
            status: components["schemas"]["JoinRequestStatus"];
            /** Createdat */
            createdAt: number;
            /** Resolvedat */
            resolvedAt: number | null;
            /** Resolvedbyteacherid */
            resolvedByTeacherId: string | null;
            /** Learnerdisplayname */
            learnerDisplayName?: string | null;
            /** Classname */
            className?: string | null;
        };
        /**
         * KnowledgeBaseDocumentListView
         * @description 当前知识库的真实文档列表。
         */
        KnowledgeBaseDocumentListView: {
            /** Items */
            items: components["schemas"]["KnowledgeBaseDocumentView"][];
        };
        /** KnowledgeBaseDocumentView */
        KnowledgeBaseDocumentView: {
            /** Id */
            id: string;
            /** Knowledgebaseid */
            knowledgeBaseId: string;
            /** Sourcedocumentid */
            sourceDocumentId: string | null;
            /** Title */
            title: string;
            /** Originalfilename */
            originalFilename: string;
            /**
             * Fileformat
             * @enum {string}
             */
            fileFormat: "pdf" | "docx" | "markdown";
            /**
             * Parsestatus
             * @enum {string}
             */
            parseStatus: "not_started" | "parsing" | "completed" | "failed";
            /** Errorcode */
            errorCode: string | null;
            /** Errormessage */
            errorMessage: string | null;
            /** Parsername */
            parserName: string | null;
            /** Parserversion */
            parserVersion: string | null;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /**
             * Version
             * @default 1
             */
            version: number;
            /** Contenthash */
            contentHash?: string | null;
            /** Markdowncontent */
            markdownContent?: string | null;
        };
        /** KnowledgeBaseImportItem */
        KnowledgeBaseImportItem: {
            /** Sourceknowledgebaseid */
            sourceKnowledgeBaseId: string;
            /** Documentids */
            documentIds: string[];
        };
        /** KnowledgeBaseImportView */
        KnowledgeBaseImportView: {
            targetKnowledgeBase: components["schemas"]["KnowledgeBaseView"];
            /** Importeddocuments */
            importedDocuments: components["schemas"]["KnowledgeBaseDocumentView"][];
            /** Skippeddocumentids */
            skippedDocumentIds: string[];
        };
        /** KnowledgeBaseIndexStatusView */
        KnowledgeBaseIndexStatusView: {
            /** Knowledgebaseid */
            knowledgeBaseId: string;
            /** Chunkcount */
            chunkCount: number;
            /** Readychunkcount */
            readyChunkCount: number;
            /** Retrievalmode */
            retrievalMode: string;
            /** Embeddingstatus */
            embeddingStatus: string;
            /** Chunkstrategyversion */
            chunkStrategyVersion: string | null;
        };
        /**
         * KnowledgeBaseKind
         * @enum {string}
         */
        KnowledgeBaseKind: "reusable" | "class_copy";
        /** KnowledgeBaseListView */
        KnowledgeBaseListView: {
            /** Items */
            items: components["schemas"]["KnowledgeBaseView"][];
        };
        /** KnowledgeBasePublicationView */
        KnowledgeBasePublicationView: {
            /** Publicationid */
            publicationId: string;
            /** Knowledgebaseid */
            knowledgeBaseId: string;
            /** Classid */
            classId: string;
            /** Version */
            version: number;
            /** Contentids */
            contentIds: string[];
            /** Createdat */
            createdAt: number;
        };
        /** KnowledgeBaseRetrievalTestRequest */
        KnowledgeBaseRetrievalTestRequest: {
            /** Query */
            query: string;
            /**
             * Mode
             * @default hybrid
             * @enum {string}
             */
            mode: "keyword" | "vector" | "hybrid";
            /**
             * Topk
             * @default 5
             */
            topK: number;
            /**
             * Minscore
             * @default 0
             */
            minScore: number;
        };
        /** KnowledgeBaseSearchRequest */
        KnowledgeBaseSearchRequest: {
            /** Query */
            query: string;
            /**
             * Limit
             * @default 8
             */
            limit: number;
        };
        /** KnowledgeBaseSearchResultView */
        KnowledgeBaseSearchResultView: {
            /** Chunkid */
            chunkId: string;
            /** Documentid */
            documentId: string;
            /** Documentfilename */
            documentFilename: string;
            /** Documentversion */
            documentVersion: number;
            /** Content */
            content: string;
            /** Titlepath */
            titlePath: string[];
            /** Pagestart */
            pageStart: number | null;
            /** Pageend */
            pageEnd: number | null;
            /** Sourceposition */
            sourcePosition: string | null;
            /** Score */
            score: number;
        };
        /** KnowledgeBaseSearchView */
        KnowledgeBaseSearchView: {
            /** Results */
            results: components["schemas"]["KnowledgeBaseSearchResultView"][];
            /** Retrievalmode */
            retrievalMode: string;
            /** Hasresults */
            hasResults: boolean;
            /**
             * Query
             * @default
             */
            query: string;
            /**
             * Topk
             * @default 5
             */
            topK: number;
            /**
             * Minscore
             * @default 0
             */
            minScore: number;
            /** Fallbackreason */
            fallbackReason?: string | null;
        };
        /** KnowledgeBaseSegmentListView */
        KnowledgeBaseSegmentListView: {
            /** Items */
            items: components["schemas"]["KnowledgeBaseSegmentView"][];
        };
        /** KnowledgeBaseSegmentPreviewRequest */
        KnowledgeBaseSegmentPreviewRequest: {
            /**
             * Mode
             * @default simple
             * @enum {string}
             */
            mode: "simple" | "advanced";
            /**
             * Maxcharacters
             * @default 2400
             */
            maxCharacters: number;
            /**
             * Overlapcharacters
             * @default 240
             */
            overlapCharacters: number;
            /** Separators */
            separators?: string[];
            /** Cleaningrules */
            cleaningRules?: string[];
            /** Documentid */
            documentId: string;
        };
        /** KnowledgeBaseSegmentPreviewView */
        KnowledgeBaseSegmentPreviewView: {
            /** Documentid */
            documentId: string;
            /** Documentversion */
            documentVersion: number;
            /**
             * Mode
             * @enum {string}
             */
            mode: "simple" | "advanced";
            /** Segments */
            segments: components["schemas"]["KnowledgeBaseSegmentView"][];
            /** Requiresrebuild */
            requiresRebuild: boolean;
        };
        /** KnowledgeBaseSegmentRebuildView */
        KnowledgeBaseSegmentRebuildView: {
            /** Knowledgebaseid */
            knowledgeBaseId: string;
            /** Documentid */
            documentId: string;
            /** Chunkcount */
            chunkCount: number;
            /**
             * Indexstatus
             * @enum {string}
             */
            indexStatus: "ready" | "failed";
            settings: components["schemas"]["KnowledgeBaseSettingsView"];
        };
        /** KnowledgeBaseSegmentView */
        KnowledgeBaseSegmentView: {
            /** Id */
            id: string;
            /** Documentid */
            documentId: string;
            /** Documentfilename */
            documentFilename: string;
            /** Documentversion */
            documentVersion: number;
            /** Ordinal */
            ordinal: number;
            /** Content */
            content: string;
            /** Titlepath */
            titlePath: string[];
            /** Pagestart */
            pageStart: number | null;
            /** Pageend */
            pageEnd: number | null;
            /** Sourceposition */
            sourcePosition: string | null;
            /**
             * Indexstatus
             * @enum {string}
             */
            indexStatus: "pending" | "ready" | "failed";
            /** Chunkstrategyversion */
            chunkStrategyVersion: string;
        };
        /** KnowledgeBaseSettingsView */
        KnowledgeBaseSettingsView: {
            /** Knowledgebaseid */
            knowledgeBaseId: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "simple" | "advanced";
            /** Maxcharacters */
            maxCharacters: number;
            /** Overlapcharacters */
            overlapCharacters: number;
            /** Separators */
            separators: string[];
            /** Cleaningrules */
            cleaningRules: string[];
            /** Indexversion */
            indexVersion: number;
            /** Updatedat */
            updatedAt: number;
        };
        /**
         * KnowledgeBaseStatus
         * @enum {string}
         */
        KnowledgeBaseStatus: "draft" | "available" | "archived";
        /** KnowledgeBaseView */
        KnowledgeBaseView: {
            /** Id */
            id: string;
            /** Ownerteacherid */
            ownerTeacherId: string;
            /** Classid */
            classId: string | null;
            /** Sourceknowledgebaseid */
            sourceKnowledgeBaseId: string | null;
            kind: components["schemas"]["KnowledgeBaseKind"];
            /** Name */
            name: string;
            /** Description */
            description: string;
            status: components["schemas"]["KnowledgeBaseStatus"];
            /** Sourceversion */
            sourceVersion: number;
            /** Documentcount */
            documentCount: number;
            /** Archivedat */
            archivedAt: number | null;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
        };
        /** KnowledgeBaseWorkspaceView */
        KnowledgeBaseWorkspaceView: {
            /** Id */
            id: string;
            /** Ownerteacherid */
            ownerTeacherId: string;
            /** Classid */
            classId: string;
            /** Sourceknowledgebaseid */
            sourceKnowledgeBaseId: string | null;
            kind: components["schemas"]["KnowledgeBaseKind"];
            /** Name */
            name: string;
            /** Description */
            description: string;
            status: components["schemas"]["KnowledgeBaseStatus"];
            /** Sourceversion */
            sourceVersion: number;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /** Documents */
            documents: components["schemas"]["KnowledgeBaseDocumentView"][];
        };
        /**
         * KnowledgePointMasteryView
         * @description 知识点掌握详情
         */
        KnowledgePointMasteryView: {
            /**
             * Knowledgepoint
             * @description 知识点
             */
            knowledgePoint: string;
            masteryLevel: components["schemas"]["MasteryLevel"];
            /**
             * Weightedscore
             * @description 加权总分
             */
            weightedScore: number;
            /**
             * Recentevidencecount
             * @description 最近有效证据数量
             */
            recentEvidenceCount: number;
            /**
             * Firstcorrectcount
             * @description 首次正确题目数量
             */
            firstCorrectCount: number;
            /**
             * Levelchange
             * @description 级别变化：-1=下降，0=不变，1=上升
             */
            levelChange: number;
            /**
             * Latestevidence
             * @description 最近证据详情，包含questionId、questionTitle、resultType、createdAt
             */
            latestEvidence?: {
                [key: string]: string | number;
            } | null;
        };
        /**
         * LearnerClassListView
         * @description 学习者正式加入的教学班列表视图。
         */
        LearnerClassListView: {
            /** Items */
            items: components["schemas"]["TeachingClassView"][];
        };
        /**
         * LearnerDetailView
         * @description 学习者详情视图
         */
        LearnerDetailView: {
            /**
             * Learnerid
             * @description 学习者ID
             */
            learnerId: string;
            /**
             * Displayname
             * @description 学习者显示名称
             */
            displayName: string;
            /** @description 完成统计 */
            completionStats: components["schemas"]["CourseCompletionStatsView"];
            masterySummary: components["schemas"]["MasterySummaryView"];
            /**
             * Simulationstatus
             * @description Webots 尚无真实实训事实
             * @default no_data
             * @constant
             */
            simulationStatus: "no_data";
        };
        /**
         * LearnerListView
         * @description 学习者列表视图
         */
        LearnerListView: {
            /**
             * Items
             * @description 学习者预览列表
             */
            items?: components["schemas"]["LearnerPreviewView"][];
        };
        /**
         * LearnerPreviewView
         * @description 学习者预览视图
         */
        LearnerPreviewView: {
            /**
             * Learnerid
             * @description 学习者ID
             */
            learnerId: string;
            /**
             * Displayname
             * @description 学习者显示名称
             */
            displayName: string;
            /**
             * Completionrate
             * @description 个人完成率（0-1）
             */
            completionRate: number;
            /**
             * Weakestknowledgepoint
             * @description 当前薄弱知识点；无结构化掌握证据时为空
             */
            weakestKnowledgePoint?: string | null;
            /**
             * Simulationstatus
             * @description Webots 尚无真实实训事实
             * @default no_data
             * @constant
             */
            simulationStatus: "no_data";
        };
        /** LoginRequest */
        LoginRequest: {
            /** Username */
            username: string;
            /** Password */
            password: string;
        };
        /**
         * MasteryDistributionView
         * @description 掌握度分布视图（匿名四级分布）
         */
        MasteryDistributionView: {
            /**
             * Unlearned
             * @description 未学习人数
             * @default 0
             */
            unlearned: number;
            /**
             * Consolidating
             * @description 巩固中人数
             * @default 0
             */
            consolidating: number;
            /**
             * Basicmastery
             * @description 基本掌握人数
             * @default 0
             */
            basicMastery: number;
            /**
             * Proficientmastery
             * @description 熟练掌握人数
             * @default 0
             */
            proficientMastery: number;
        };
        /**
         * MasteryLevel
         * @description 掌握度级别
         * @enum {string}
         */
        MasteryLevel: "unlearned" | "consolidating" | "basic_mastery" | "proficient_mastery";
        /**
         * MasterySummaryView
         * @description 掌握度摘要
         */
        MasterySummaryView: {
            /**
             * Status
             * @default success
             */
            status: string;
            /**
             * Message
             * @default 掌握度分析完成
             */
            message: string;
            /**
             * Totalknowledgepoints
             * @description 总知识点数量
             * @default 0
             */
            totalKnowledgePoints: number;
            /**
             * Leveldistribution
             * @description 各级别知识点数量分布
             */
            levelDistribution?: {
                [key: string]: number;
            };
            /**
             * Knowledgepoints
             * @description 知识点掌握详情列表
             */
            knowledgePoints?: components["schemas"]["KnowledgePointMasteryView"][];
            /**
             * Nextsuggestion
             * @description 下一步学习建议
             * @default
             */
            nextSuggestion: string;
        };
        /** PairingBindRequest */
        PairingBindRequest: {
            /** Pairingtoken */
            pairingToken: string;
            /** Connectorid */
            connectorId: string;
        };
        /** PairingView */
        PairingView: {
            /** Pairingtoken */
            pairingToken: string;
            /** Expiresat */
            expiresAt: number;
            /**
             * Source
             * @default demo
             * @constant
             */
            source: "demo";
        };
        /**
         * ParseStatus
         * @description 解析状态
         * @enum {string}
         */
        ParseStatus: "not_started" | "parsing" | "completed" | "timed_out" | "failed";
        /**
         * PreparationSessionParagraphView
         * @description 创建教师可读取的知识库分段。
         */
        PreparationSessionParagraphView: {
            /** Ordinal */
            ordinal: number;
            /** Documentid */
            documentId?: string | null;
            /** Documentfilename */
            documentFilename?: string | null;
            /** Blocktype */
            blockType: string;
            /** Content */
            content: string;
        };
        /**
         * PreparationSessionParagraphWithHighlightsView
         * @description 带教学重点的知识库分段视图
         */
        PreparationSessionParagraphWithHighlightsView: {
            /** Ordinal */
            ordinal: number;
            /** Documentid */
            documentId?: string | null;
            /** Documentfilename */
            documentFilename?: string | null;
            /** Blocktype */
            blockType: string;
            /** Content */
            content: string;
            /** Highlights */
            highlights: components["schemas"]["HighlightView"][];
            /** Hashighlights */
            hasHighlights: boolean;
        };
        /**
         * PreparationSessionParsingResultView
         * @description 仅在解析成功后返回有序段落。
         */
        PreparationSessionParsingResultView: {
            session: components["schemas"]["PreparationSessionView"];
            /** Paragraphs */
            paragraphs: components["schemas"]["PreparationSessionParagraphView"][];
        };
        /**
         * PreparationSessionParsingResultWithHighlightsView
         * @description 带教学重点的解析结果视图
         */
        PreparationSessionParsingResultWithHighlightsView: {
            session: components["schemas"]["PreparationSessionView"];
            /** Paragraphs */
            paragraphs: components["schemas"]["PreparationSessionParagraphWithHighlightsView"][];
            /** Totalhighlights */
            totalHighlights: number;
        };
        /**
         * PreparationSessionView
         * @description 备课会话视图
         */
        PreparationSessionView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            /** Originalfilename */
            originalFilename: string | null;
            fileFormat: components["schemas"]["FileFormat"] | null;
            /** Filesizebytes */
            fileSizeBytes: number | null;
            uploadStatus: components["schemas"]["UploadStatus"];
            parseStatus: components["schemas"]["ParseStatus"];
            currentStep: components["schemas"]["CurrentStep"];
            /** Parsedcontentreference */
            parsedContentReference: string | null;
            /** Parseerrorcode */
            parseErrorCode?: string | null;
            /** Parsestartedat */
            parseStartedAt?: number | null;
            /** Parsecompletedat */
            parseCompletedAt?: number | null;
            /**
             * Highlightsjson
             * @default []
             */
            highlightsJson: string;
            /** Candidatequestionsjson */
            candidateQuestionsJson: string;
            /** Publicationdraftjson */
            publicationDraftJson: string;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /** Knowledgebaseid */
            knowledgeBaseId?: string | null;
            /** Selecteddocumentids */
            selectedDocumentIds?: string[];
        };
        /** ProtocolEnvelope */
        ProtocolEnvelope: {
            /**
             * Protocolversion
             * @constant
             */
            protocolVersion: "webots-demo-v1";
            /** Messageid */
            messageId: string;
            /**
             * Messagetype
             * @enum {string}
             */
            messageType: "environment" | "command" | "event" | "result";
            /** Runid */
            runId?: string | null;
            /** Epoch */
            epoch: number;
            /** Eventsequence */
            eventSequence?: number | null;
            /** Payload */
            payload?: {
                [key: string]: unknown;
            };
        };
        /**
         * PublishHomeworkRequest
         * @description 发布作业请求
         */
        PublishHomeworkRequest: {
            /** Title */
            title: string;
            /**
             * Dueat
             * @description 截止时间（Unix时间戳）
             */
            dueAt: number;
            /**
             * Description
             * @default
             */
            description: string;
        };
        /**
         * PublishHomeworkResponse
         * @description 作业发布响应
         */
        PublishHomeworkResponse: {
            session: components["schemas"]["PreparationSessionView"];
            /** Homeworkid */
            homeworkId: string;
        };
        /**
         * PublishQuestionRequest
         * @description 逐题发布请求。
         */
        PublishQuestionRequest: {
            /**
             * Mode
             * @enum {string}
             */
            mode: "classroom" | "homework";
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Dueat
             * @description 作业截止时间（Unix时间戳）
             */
            dueAt?: number | null;
            /**
             * Description
             * @default
             */
            description: string;
        };
        /**
         * PublishedContentDetailView
         * @description 已发布内容详情视图，包含教学重点和来源信息
         */
        PublishedContentDetailView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            contentType: components["schemas"]["ContentType"];
            /** Publicationstatus */
            publicationStatus: string;
            /** Title */
            title: string;
            /** Content */
            content: string;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /** Dueat */
            dueAt?: number | null;
            /** Description */
            description?: string | null;
            /**
             * Highlightsjson
             * @default []
             */
            highlightsJson: string;
            /** Sourcepreparationsessionid */
            sourcePreparationSessionId?: string | null;
            /** Sourceteacherid */
            sourceTeacherId?: string | null;
            /** Sourcefilename */
            sourceFilename?: string | null;
            question?: components["schemas"]["PublishedQuestionView"] | null;
            /**
             * Completed
             * @default false
             */
            completed: boolean;
        };
        /**
         * PublishedContentListView
         * @description 已发布内容列表视图
         */
        PublishedContentListView: {
            /** Items */
            items: components["schemas"]["PublishedContentView"][];
        };
        /**
         * PublishedContentView
         * @description 已发布内容视图
         */
        PublishedContentView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            contentType: components["schemas"]["ContentType"];
            /** Publicationstatus */
            publicationStatus: string;
            /** Title */
            title: string;
            /** Content */
            content: string;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /**
             * Completed
             * @default false
             */
            completed: boolean;
            /** Dueat */
            dueAt?: number | null;
            /** Description */
            description?: string | null;
            question?: components["schemas"]["PublishedQuestionView"] | null;
        };
        /**
         * PublishedQuestionView
         * @description 学习者可见的结构化题目，不包含判分答案与解析。
         */
        PublishedQuestionView: {
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /** Knowledgepoints */
            knowledgePoints?: string[];
            /**
             * Hint
             * @default
             */
            hint: string;
        };
        /**
         * QuestionListView
         * @description 题目列表视图
         */
        QuestionListView: {
            /** Items */
            items: components["schemas"]["QuestionView"][];
            /**
             * Ispublishunlocked
             * @default false
             */
            isPublishUnlocked: boolean;
            /**
             * Cangeneratefromhighlights
             * @default false
             */
            canGenerateFromHighlights: boolean;
        };
        /**
         * QuestionPublicationView
         * @description 逐题发布结果。
         */
        QuestionPublicationView: {
            /** Questionid */
            questionId: string;
            /** Contentid */
            contentId: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "classroom" | "homework";
            /** Homeworkid */
            homeworkId?: string | null;
            /** Createdat */
            createdAt: number;
        };
        /**
         * QuestionReviewStatus
         * @description 题目审核状态
         * @enum {string}
         */
        QuestionReviewStatus: "candidate" | "confirmed";
        /**
         * QuestionSource
         * @description 题目来源
         * @enum {string}
         */
        QuestionSource: "manual" | "candidate";
        /**
         * QuestionType
         * @description 题目类型
         * @enum {string}
         */
        QuestionType: "single_choice" | "multiple_choice";
        /**
         * QuestionView
         * @description 题目视图
         */
        QuestionView: {
            /** Id */
            id: string;
            source: components["schemas"]["QuestionSource"];
            reviewStatus: components["schemas"]["QuestionReviewStatus"];
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /** Answers */
            answers: number[];
            /** Knowledgepoints */
            knowledgePoints: string[];
            /** Highlightsourceids */
            highlightSourceIds: string[];
            /** Hint */
            hint: string;
            /** Explanation */
            explanation: string;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /**
             * Publishedclassroom
             * @default false
             */
            publishedClassroom: boolean;
            /**
             * Publishedhomework
             * @default false
             */
            publishedHomework: boolean;
        };
        /** RegisterRequest */
        RegisterRequest: {
            /** Username */
            username: string;
            /** Password */
            password: string;
            /** Displayname */
            displayName: string;
            role: components["schemas"]["UserRole"];
        };
        /**
         * RemoveHighlightRequest
         * @description 取消教学重点请求
         */
        RemoveHighlightRequest: {
            /** Highlightid */
            highlightId: string;
        };
        /**
         * RenameTeachingClassRequest
         * @description 教师重命名教学班请求。
         */
        RenameTeachingClassRequest: {
            /** Name */
            name: string;
        };
        /**
         * ResolveJoinRequestRequest
         * @description 处理加入申请请求
         */
        ResolveJoinRequestRequest: {
            /** @description 只能是approved或rejected */
            status: components["schemas"]["JoinRequestStatus"];
        };
        /**
         * ResolveJoinRequestResponse
         * @description 处理加入申请响应
         */
        ResolveJoinRequestResponse: {
            /** Requestid */
            requestId: string;
            /** Classid */
            classId: string;
            /** Learnerid */
            learnerId: string;
            status: components["schemas"]["JoinRequestStatus"];
            /** Resolvedat */
            resolvedAt: number;
            /** Resolvedbyteacherid */
            resolvedByTeacherId: string;
            /** Membershipcreated */
            membershipCreated: boolean;
        };
        /**
         * ResultType
         * @description 结果类型
         * @enum {string}
         */
        ResultType: "first_correct" | "hint_correct" | "final_wrong" | "abandoned";
        /** RunCommandRequest */
        RunCommandRequest: {
            /**
             * Command
             * @enum {string}
             */
            command: "start" | "reset" | "hard_reset" | "fail";
        };
        /** RunCreateRequest */
        RunCreateRequest: {
            /** Connectorid */
            connectorId: string;
            /**
             * Taskid
             * @default
             */
            taskId: string;
        };
        /** RunEventRequest */
        RunEventRequest: {
            /** Epoch */
            epoch: number;
            /** Sequence */
            sequence: number;
            /** Eventtype */
            eventType: string;
            /** Payload */
            payload?: {
                [key: string]: unknown;
            };
        };
        /** RunResultRequest */
        RunResultRequest: {
            /** Epoch */
            epoch: number;
            /**
             * Status
             * @enum {string}
             */
            status: "completed" | "failed";
            /** Result */
            result?: {
                [key: string]: unknown;
            };
        };
        /** RunView */
        RunView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            /** Learnerid */
            learnerId: string;
            /** Connectorid */
            connectorId: string;
            /** Taskid */
            taskId: string;
            /**
             * Status
             * @enum {string}
             */
            status: "created" | "dispatched" | "running" | "completed" | "failed";
            /** Epoch */
            epoch: number;
            /** Nexteventsequence */
            nextEventSequence: number;
            /**
             * Source
             * @default demo
             * @constant
             */
            source: "demo";
            /** Result */
            result?: {
                [key: string]: unknown;
            } | null;
        };
        /**
         * SaveHomeworkDraftBody
         * @description 保存作业草稿 HTTP 请求体；class_id/homework_id 以路径参数为唯一来源
         */
        SaveHomeworkDraftBody: {
            /** Answers */
            answers?: {
                [key: string]: number[];
            };
        };
        /**
         * SelectPreparationDocumentsRequest
         * @description 从当前教学班知识库选择已完成索引的文档。
         */
        SelectPreparationDocumentsRequest: {
            /** Documentids */
            documentIds: string[];
        };
        /**
         * SimulationSummaryView
         * @description 只暴露 Webots 协议产生的结构化摘要，不暴露事件正文或本机路径。
         */
        SimulationSummaryView: {
            /**
             * Source
             * @default demo
             * @constant
             */
            source: "demo";
            /**
             * Taskstatus
             * @default no_tasks
             * @enum {string}
             */
            taskStatus: "no_tasks" | "configured";
            /**
             * Connectorcount
             * @default 0
             */
            connectorCount: number;
            /**
             * Runcount
             * @default 0
             */
            runCount: number;
            /**
             * Runningcount
             * @default 0
             */
            runningCount: number;
            /**
             * Completedcount
             * @default 0
             */
            completedCount: number;
            /**
             * Failedcount
             * @default 0
             */
            failedCount: number;
            /** Latestterminalstatus */
            latestTerminalStatus?: ("completed" | "failed") | null;
            /** Latestresult */
            latestResult?: {
                [key: string]: unknown;
            } | null;
        };
        /**
         * SubmitHomeworkBody
         * @description 提交作业 HTTP 请求体；class_id/homework_id 以路径参数为唯一来源
         */
        SubmitHomeworkBody: {
            /** Answers */
            answers?: {
                [key: string]: number[];
            };
        };
        /** TaskCatalogView */
        TaskCatalogView: {
            /** Items */
            items: {
                [key: string]: string;
            }[];
            /**
             * Source
             * @default demo
             * @constant
             */
            source: "demo";
        };
        /**
         * TeacherAIAnalysisView
         * @description 小 B 模型分析结果，不携带学习者身份字段。
         */
        TeacherAIAnalysisView: {
            /** Analysis */
            analysis?: string | null;
            /** Suggestions */
            suggestions?: string[];
            /**
             * Source
             * @enum {string}
             */
            source: "integrated" | "demo" | "unconfigured" | "degraded";
        };
        /**
         * TeacherDashboardConsolidationView
         * @description 待巩固知识点视图
         */
        TeacherDashboardConsolidationView: {
            /**
             * Knowledgepoint
             * @description 知识点
             */
            knowledgePoint: string;
            /**
             * Learnerscount
             * @description 需要巩固的学习者数
             */
            learnersCount: number;
            /**
             * Averagemastery
             * @description 平均掌握度分数
             */
            averageMastery: number;
        };
        /**
         * TeacherDashboardHomeworkSummaryView
         * @description 作业摘要视图
         */
        TeacherDashboardHomeworkSummaryView: {
            /**
             * Totalhomeworks
             * @description 总作业数
             * @default 0
             */
            totalHomeworks: number;
            /**
             * Expectedsubmissions
             * @description 应提交总份数
             * @default 0
             */
            expectedSubmissions: number;
            /**
             * Pendingsubmissions
             * @description 待提交数
             * @default 0
             */
            pendingSubmissions: number;
            /**
             * Submittedsubmissions
             * @description 已提交份数
             * @default 0
             */
            submittedSubmissions: number;
            /**
             * Latesubmissions
             * @description 迟交份数
             * @default 0
             */
            lateSubmissions: number;
            /**
             * Averagescore
             * @description 已提交作业平均得分
             */
            averageScore?: number | null;
        };
        /**
         * TeacherDashboardLearnerPreviewView
         * @description 教师dashboard学习者预览视图
         */
        TeacherDashboardLearnerPreviewView: {
            /**
             * Learnerid
             * @description 学习者ID
             */
            learnerId: string;
            /**
             * Displayname
             * @description 学习者显示名称
             */
            displayName: string;
            /**
             * Completionrate
             * @description 个人完成率（0-1）
             */
            completionRate: number;
            /** @description 主要掌握度级别 */
            masteryLevel: components["schemas"]["MasteryLevel"];
            /**
             * Lastactivity
             * @description 最后活动时间
             */
            lastActivity?: number | null;
        };
        /**
         * TeacherDashboardView
         * @description 教师专用dashboard视图
         */
        TeacherDashboardView: {
            /**
             * Totalmembers
             * @description 班级正式成员总数
             * @default 0
             */
            totalMembers: number;
            /**
             * Contentcompletionrate
             * @description 课件平均完成率（0-1）
             * @default 0
             */
            contentCompletionRate: number;
            /**
             * Atleastonecompleted
             * @description 至少完成一项内容的人数
             * @default 0
             */
            atLeastOneCompleted: number;
            /** @description 掌握度分布 */
            masteryDistribution?: components["schemas"]["MasteryDistributionView"];
            /**
             * Questionsstatus
             * @description 当前没有结构化学习者提问事实
             * @default no_data
             * @constant
             */
            questionsStatus: "no_data";
            /**
             * Consolidationtopics
             * @description 待巩固知识点列表
             */
            consolidationTopics?: components["schemas"]["TeacherDashboardConsolidationView"][];
            /** @description 作业摘要 */
            homeworkSummary?: components["schemas"]["TeacherDashboardHomeworkSummaryView"];
            /**
             * Simulationstatus
             * @description Webots 尚无真实实训事实
             * @default no_data
             * @constant
             */
            simulationStatus: "no_data";
            /**
             * Learnerpreviews
             * @description 学习者预览列表
             */
            learnerPreviews?: components["schemas"]["TeacherDashboardLearnerPreviewView"][];
            /**
             * Insufficientsample
             * @description 样本不足标记
             * @default false
             */
            insufficientSample: boolean;
            /**
             * Nodata
             * @description 无数据标记
             * @default false
             */
            noData: boolean;
        };
        /**
         * TeacherHomeworkListView
         * @description 教师作业管理列表视图。
         */
        TeacherHomeworkListView: {
            /** Items */
            items?: components["schemas"]["TeacherHomeworkStatsView"][];
            /**
             * Nodata
             * @description 当前班没有已发布作业
             * @default false
             */
            noData: boolean;
        };
        /**
         * TeacherHomeworkQuestionStatsView
         * @description 教师作业逐题统计视图。
         */
        TeacherHomeworkQuestionStatsView: {
            /**
             * Questionid
             * @description 题目ID
             */
            questionId: string;
            /**
             * Questioncontent
             * @description 题目内容
             */
            questionContent: string;
            /**
             * Totalattempts
             * @description 已判分作答次数
             * @default 0
             */
            totalAttempts: number;
            /**
             * Correctattempts
             * @description 判分正确次数
             * @default 0
             */
            correctAttempts: number;
            /**
             * Correctrate
             * @description 正确率（0-100）；无数据时为空
             */
            correctRate?: number | null;
            /**
             * Commonerrorreason
             * @description 结构化答案差异归纳的常见错因
             */
            commonErrorReason?: string | null;
        };
        /**
         * TeacherHomeworkStatsView
         * @description 教师单份作业统计视图。
         */
        TeacherHomeworkStatsView: {
            /** @description 已发布作业 */
            homework: components["schemas"]["PublishedContentView"];
            /**
             * Status
             * @description 作业发布状态
             * @default published
             * @constant
             */
            status: "published";
            /**
             * Totallearners
             * @description 当前班正式成员数
             * @default 0
             */
            totalLearners: number;
            /**
             * Submittedcount
             * @description 已提交人数
             * @default 0
             */
            submittedCount: number;
            /**
             * Submittedlearnerids
             * @description 已提交该作业的学习者 ID
             */
            submittedLearnerIds?: string[];
            /**
             * Latecount
             * @description 迟交人数
             * @default 0
             */
            lateCount: number;
            /**
             * Correctrate
             * @description 作业整体正确率（0-100）；无数据时为空
             */
            correctRate?: number | null;
            /**
             * Pendingreviewcount
             * @description 缺少确定性判分结果的提交数
             * @default 0
             */
            pendingReviewCount: number;
            /**
             * Datastatus
             * @description 统计数据状态
             * @default no_submissions
             * @enum {string}
             */
            dataStatus: "ready" | "no_submissions" | "insufficient_data";
            /**
             * Questionstats
             * @description 逐题统计
             */
            questionStats?: components["schemas"]["TeacherHomeworkQuestionStatsView"][];
            /**
             * Aianalysis
             * @description AI 作业整体分析（含知识点掌握情况和常见问题）
             */
            aiAnalysis?: string | null;
            /**
             * Aisuggestions
             * @description AI 学习建议列表
             */
            aiSuggestions?: string[];
        };
        /** TeacherPublishedContentListView */
        TeacherPublishedContentListView: {
            /** Items */
            items: components["schemas"]["TeacherPublishedContentView"][];
        };
        /**
         * TeacherPublishedContentView
         * @description 教师已发布内容视图。
         */
        TeacherPublishedContentView: {
            /** Id */
            id: string;
            /** Classid */
            classId: string;
            contentType: components["schemas"]["ContentType"];
            /** Publicationstatus */
            publicationStatus: string;
            /** Title */
            title: string;
            /** Content */
            content: string;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
            /**
             * Completed
             * @default false
             */
            completed: boolean;
            /** Dueat */
            dueAt?: number | null;
            /** Description */
            description?: string | null;
            question?: components["schemas"]["TeacherPublishedQuestionView"] | null;
        };
        /**
         * TeacherPublishedQuestionView
         * @description 仅教师已发布内容接口可见的完整题目事实。
         */
        TeacherPublishedQuestionView: {
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /** Knowledgepoints */
            knowledgePoints?: string[];
            /**
             * Hint
             * @default
             */
            hint: string;
            /** Answers */
            answers: number[];
            /**
             * Explanation
             * @default
             */
            explanation: string;
        };
        /**
         * TeachingClassListView
         * @description 教学班列表视图
         */
        TeachingClassListView: {
            /** Items */
            items: components["schemas"]["TeachingClassView"][];
        };
        /**
         * TeachingClassView
         * @description 教学班视图
         */
        TeachingClassView: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            joinPolicy: components["schemas"]["JoinPolicy"];
            /** Membercount */
            memberCount: number;
            /** Createdat */
            createdAt: number;
            /** Updatedat */
            updatedAt: number;
        };
        /**
         * UpdateCourseOverviewRequest
         * @description 更新课程概述请求
         */
        UpdateCourseOverviewRequest: {
            /**
             * Background
             * @default
             */
            background: string;
            /**
             * Introduction
             * @default
             */
            introduction: string;
            /**
             * Objectives
             * @default
             */
            objectives: string;
            /**
             * Features
             * @default
             */
            features: string;
        };
        /**
         * UpdateJoinPolicyRequest
         * @description 更新加入策略请求
         */
        UpdateJoinPolicyRequest: {
            joinPolicy: components["schemas"]["JoinPolicy"];
        };
        /**
         * UpdateKnowledgeBaseDocumentRequest
         * @description 文档元数据或规范化 Markdown 的编辑请求。
         */
        UpdateKnowledgeBaseDocumentRequest: {
            /** Title */
            title?: string | null;
            /** Markdowncontent */
            markdownContent?: string | null;
        };
        /** UpdateKnowledgeBaseRequest */
        UpdateKnowledgeBaseRequest: {
            /** Name */
            name?: string | null;
            /** Description */
            description?: string | null;
        };
        /** UpdateKnowledgeBaseSettingsRequest */
        UpdateKnowledgeBaseSettingsRequest: {
            /**
             * Mode
             * @default simple
             * @enum {string}
             */
            mode: "simple" | "advanced";
            /**
             * Maxcharacters
             * @default 2400
             */
            maxCharacters: number;
            /**
             * Overlapcharacters
             * @default 240
             */
            overlapCharacters: number;
            /** Separators */
            separators?: string[];
            /** Cleaningrules */
            cleaningRules?: string[];
        };
        /**
         * UpdatePublishedContentRequest
         * @description 教师修改已发布课堂练习或作业请求。
         */
        UpdatePublishedContentRequest: {
            /** Title */
            title: string;
            /** Description */
            description?: string | null;
            /**
             * Dueat
             * @description 作业截止时间（Unix时间戳）
             */
            dueAt?: number | null;
            /** Stem */
            stem?: string | null;
            /** Options */
            options?: string[] | null;
            /** Answers */
            answers?: number[] | null;
            /** Knowledgepoints */
            knowledgePoints?: string[] | null;
            /** Hint */
            hint?: string | null;
            /** Explanation */
            explanation?: string | null;
        };
        /**
         * UpdateQuestionRequest
         * @description 更新题目请求
         */
        UpdateQuestionRequest: {
            type: components["schemas"]["QuestionType"];
            /** Stem */
            stem: string;
            /** Options */
            options: string[];
            /** Answers */
            answers: number[];
            /** Knowledgepoints */
            knowledgePoints: string[];
            /** Highlightsourceids */
            highlightSourceIds: string[];
            /**
             * Hint
             * @default
             */
            hint: string;
            /**
             * Explanation
             * @default
             */
            explanation: string;
        };
        /**
         * UploadStatus
         * @description 上传状态
         * @enum {string}
         */
        UploadStatus: "waiting" | "uploaded";
        /**
         * UserRole
         * @enum {string}
         */
        UserRole: "learner" | "teacher";
        /** UserView */
        UserView: {
            /** Id */
            id: string;
            /** Username */
            username: string;
            /** Displayname */
            displayName: string;
            role: components["schemas"]["UserRole"];
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** WorkspaceView */
        WorkspaceView: {
            role: components["schemas"]["UserRole"];
            /** Title */
            title: string;
            /** Navigation */
            navigation: string[];
        };
        /**
         * XiaodChatRequest
         * @description 小D伴学提问输入，携带当前课程内容的最小上下文和回答模式。
         */
        XiaodChatRequest: {
            /** Classid */
            classId: string;
            /** Contentid */
            contentId: string;
            /** Question */
            question: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "explain" | "guide";
        };
        /**
         * XiaodChatView
         * @description 小D伴学应答与来源状态。
         */
        XiaodChatView: {
            /** Text */
            text: string;
            /**
             * Status
             * @enum {string}
             */
            status: "success" | "degraded";
            /**
             * Source
             * @enum {string}
             */
            source: "integrated" | "demo" | "unconfigured" | "degraded";
            /** Failurecode */
            failureCode?: string | null;
            /**
             * References
             * @description 引用来源的分段标题路径列表
             */
            references?: string[] | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    register_api_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_AuthPayload_"];
                };
            };
            /** @description 用户名已存在 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    login_api_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_AuthPayload_"];
                };
            };
            /** @description 用户名或密码错误 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_me_api_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_UserView_"];
                };
            };
            /** @description 登录状态已失效 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    logout_api_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 登录状态已失效 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_learner_workspace_api_workspaces_learner_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_WorkspaceView_"];
                };
            };
            /** @description 登录状态已失效 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 角色无权访问 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_teacher_workspace_api_workspaces_teacher_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_WorkspaceView_"];
                };
            };
            /** @description 登录状态已失效 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 角色无权访问 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_knowledge_bases_api_knowledge_bases_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseListView_"];
                };
            };
            /** @description 只有教师可以查看课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_knowledge_base_api_knowledge_bases_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateKnowledgeBaseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseView_"];
                };
            };
            /** @description 只有教师可以管理课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库名称已存在 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_knowledge_base_api_knowledge_bases__knowledge_base_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseView_"];
                };
            };
            /** @description 只有教师可以查看课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    delete_knowledge_base_api_knowledge_bases__knowledge_base_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以删除课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库已有教学班副本，不能删除来源知识库 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_knowledge_base_api_knowledge_bases__knowledge_base_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateKnowledgeBaseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseView_"];
                };
            };
            /** @description 至少提供一个需要更新的字段 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以更新课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库名称已存在 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    archive_knowledge_base_api_knowledge_bases__knowledge_base_id__archive_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseView_"];
                };
            };
            /** @description 只有教师可以归档课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    copy_knowledge_base_to_class_api_knowledge_bases__knowledge_base_id__copies_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CopyKnowledgeBaseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseView_"];
                };
            };
            /** @description 只有教师可以复制课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库或教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不能复制到该教学班 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    import_knowledge_base_documents_api_knowledge_bases_imports_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImportKnowledgeBaseDocumentsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseImportView_"];
                };
            };
            /** @description 只有教师可以导入知识库文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 来源文档或教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库文档导入失败 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    publish_knowledge_base_api_knowledge_bases__knowledge_base_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBasePublicationView_"];
                };
            };
            /** @description 没有权限发布知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库尚未准备好发布 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    search_knowledge_base_api_knowledge_bases__knowledge_base_id__search_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KnowledgeBaseSearchRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSearchView_"];
                };
            };
            /** @description 只有教师可以检索课件知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    test_knowledge_base_retrieval_api_knowledge_bases__knowledge_base_id__retrieval_tests_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KnowledgeBaseRetrievalTestRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSearchView_"];
                };
            };
            /** @description 只有教师可以测试知识库召回 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_knowledge_base_index_status_api_knowledge_bases__knowledge_base_id__index_status_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseIndexStatusView_"];
                };
            };
            /** @description 没有权限查看索引状态 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_knowledge_base_documents_api_knowledge_bases__knowledge_base_id__documents_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseDocumentListView_"];
                };
            };
            /** @description 没有权限查看知识库文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    upload_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseDocumentView_"];
                };
            };
            /** @description 文件为空或格式不支持 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 没有权限修改知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseDocumentView_"];
                };
            };
            /** @description 没有权限查看知识库文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    delete_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 没有权限删除知识库文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
                document_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateKnowledgeBaseDocumentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseDocumentView_"];
                };
            };
            /** @description 文档修改内容不正确 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 没有权限修改知识库文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    replace_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__replace_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
                document_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_replace_knowledge_base_document_api_knowledge_bases__knowledge_base_id__documents__document_id__replace_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseDocumentView_"];
                };
            };
            /** @description 文件为空或格式不支持 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 没有权限修改知识库文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_knowledge_base_settings_api_knowledge_bases__knowledge_base_id__settings_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSettingsView_"];
                };
            };
            /** @description 没有权限查看知识库设置 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_knowledge_base_settings_api_knowledge_bases__knowledge_base_id__settings_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateKnowledgeBaseSettingsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSettingsView_"];
                };
            };
            /** @description 分段参数不正确 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 没有权限修改知识库设置 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    preview_knowledge_base_segments_api_knowledge_bases__knowledge_base_id__segments_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KnowledgeBaseSegmentPreviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSegmentPreviewView_"];
                };
            };
            /** @description 没有权限预览知识库分段 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档尚未准备好 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    rebuild_knowledge_base_segments_api_knowledge_bases__knowledge_base_id__segments_rebuild_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KnowledgeBaseSegmentPreviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSegmentRebuildView_"];
                };
            };
            /** @description 没有权限重建知识库分段 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 文档尚未准备好 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_knowledge_base_segments_api_knowledge_bases__knowledge_base_id__segments_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                knowledge_base_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSegmentListView_"];
                };
            };
            /** @description 没有权限查看知识库分段 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 知识库不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    retry_knowledge_base_document_api_knowledge_bases_documents__document_id__retry_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseDocumentView_"];
                };
            };
            /** @description 失败文档不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_teaching_classes_api_teaching_classes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeachingClassListView_"];
                };
            };
            /** @description 只有教师可以查看教学班列表 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_teaching_class_api_teaching_classes_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateTeachingClassRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeachingClassView_"];
                };
            };
            /** @description 只有教师可以创建教学班 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_join_policy_api_teaching_classes__class_id__join_policy_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateJoinPolicyRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeachingClassView_"];
                };
            };
            /** @description 只有教师可以修改教学班 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    rename_teaching_class_api_teaching_classes__class_id__name_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RenameTeachingClassRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeachingClassView_"];
                };
            };
            /** @description 只有课程教师可以重命名课程 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_teaching_class_api_teaching_classes__class_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeachingClassView_"];
                };
            };
            /** @description 只有教师可以查看教学班详情 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    delete_teaching_class_api_teaching_classes__class_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有课程教师可以删除课程 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    discover_classes_api_teaching_classes_discover_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DiscoverableClassListView_"];
                };
            };
            /** @description 只有学习者可以访问发现功能 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_learner_classes_api_teaching_classes_mine_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_LearnerClassListView_"];
                };
            };
            /** @description 只有学习者可以查看我的课程 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    join_class_api_teaching_classes__class_id__join_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_JoinClassResponse_"];
                };
            };
            /** @description 只有学习者可以加入教学班 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_join_request_api_teaching_classes__class_id__join_request_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CreateJoinRequestResponse_"];
                };
            };
            /** @description 申请已存在或已是成员 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有学习者可以提交申请 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_pending_join_requests_api_teaching_classes__class_id__join_requests_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_JoinRequestListView_"];
                };
            };
            /** @description 只有班级教师可以查看申请 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    resolve_join_request_api_teaching_classes_join_requests__request_id__resolve_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResolveJoinRequestRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResolveJoinRequestResponse_"];
                };
            };
            /** @description 申请已被处理 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级教师可以处理申请 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 申请不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_learner_join_requests_api_teaching_classes_join_requests_mine_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_JoinRequestListView_"];
                };
            };
            /** @description 只有学习者可以查看自己的申请 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_authorization_code_api_teaching_classes__class_id__authorization_code_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_Union_AuthorizationCodeView__NoneType__"];
                };
            };
            /** @description 只有班级教师可以查看授权码 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_or_update_authorization_code_api_teaching_classes__class_id__authorization_code_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateOrUpdateAuthorizationCodeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_AuthorizationCodeView_"];
                };
            };
            /** @description 过期时间无效 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级教师可以管理授权码 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    join_class_by_authorization_code_api_teaching_classes_join_by_authorization_code_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JoinByAuthorizationCodeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_JoinClassResponse_"];
                };
            };
            /** @description 授权码无效 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有学习者可以使用授权码加入 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_class_knowledge_base_api_teaching_classes__class_id__knowledge_base_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_Union_KnowledgeBaseWorkspaceView__NoneType__"];
                };
            };
            /** @description 只有班级教师可以查看知识库 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    search_class_knowledge_base_api_teaching_classes__class_id__knowledge_base_search_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KnowledgeBaseSearchRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_KnowledgeBaseSearchView_"];
                };
            };
            /** @description 教学班不存在或无权访问 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_course_overview_api_teaching_classes__class_id__course_overview_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CourseOverview_"];
                };
            };
            /** @description 只有班级教师可以查看课程概述 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_course_overview_api_teaching_classes__class_id__course_overview_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateCourseOverviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CourseOverview_"];
                };
            };
            /** @description 只有班级教师可以更新课程概述 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    generate_course_overview_candidates_api_teaching_classes__class_id__course_overview_candidates_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CourseOverviewCandidateView_"];
                };
            };
            /** @description 只有班级教师可以生成课程概述候选 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_published_contents_api_teaching_classes__class_id__published_contents_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeacherPublishedContentListView_"];
                };
            };
            /** @description 只有班级教师可以查看已发布内容 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_published_content_api_teaching_classes__class_id__published_contents__content_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdatePublishedContentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeacherPublishedContentView_"];
                };
            };
            /** @description 课程内容字段或类型不合法 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以修改已发布内容 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 课程内容不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 题目结构不完整 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    delete_published_content_api_teaching_classes__class_id__published_contents__content_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 当前课程内容类型不支持删除 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以删除已发布内容 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 课程内容不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_published_contents_for_learner_api_teaching_classes__class_id__published_contents_learner_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PublishedContentListView_"];
                };
            };
            /** @description 只有班级正式成员可以查看已发布内容 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_published_content_detail_for_learner_api_teaching_classes__class_id__published_contents__content_id__learner_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PublishedContentDetailView_"];
                };
            };
            /** @description 只有班级正式成员可以查看课程内容 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 课程内容不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    mark_content_complete_api_teaching_classes__class_id__contents__content_id__complete_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CourseContentCompletionView_"];
                };
            };
            /** @description 作业和课堂练习必须提交后自动完成 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以标记内容完成 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 课程内容不存在或未发布 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_course_home_summary_api_teaching_classes__class_id__home_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CourseHomeSummaryView_"];
                };
            };
            /** @description 只有班级正式成员可以查看课程首页汇总 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_preparation_session_api_teaching_classes__class_id__preparation_session_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 只有教师可以查看备课会话 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_or_get_preparation_session_api_teaching_classes__class_id__preparation_session_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 备课会话创建成功 */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 只有教师可以创建备课会话 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_preparation_session_upload_api_teaching_classes__class_id__preparation_session_upload_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_update_preparation_session_upload_api_teaching_classes__class_id__preparation_session_upload_put"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 只有教师可以上传文件 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    start_preparation_session_parsing_api_teaching_classes__class_id__preparation_session_parse_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_preparation_session_parsed_paragraphs_api_teaching_classes__class_id__preparation_session_parsed_paragraphs_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionParsingResultView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_preparation_session_parsed_paragraphs_with_highlights_api_teaching_classes__class_id__preparation_session_parsed_paragraphs_with_highlights_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionParsingResultWithHighlightsView_"];
                };
            };
            /** @description 只有教师可以查看备课会话 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    add_highlight_api_teaching_classes__class_id__preparation_session_highlights_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AddHighlightRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_HighlightView_"];
                };
            };
            /** @description 教学重点添加失败 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以添加教学重点 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话或段落不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学重点冲突 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    remove_highlight_api_teaching_classes__class_id__preparation_session_highlights_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RemoveHighlightRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学重点取消失败 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以取消教学重点 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学重点不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_questions_api_teaching_classes__class_id__preparation_session_questions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_QuestionListView_"];
                };
            };
            /** @description 只有教师可以查看题目 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_question_api_teaching_classes__class_id__preparation_session_questions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateQuestionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_QuestionView_"];
                };
            };
            /** @description 题目创建失败 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以创建题目 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    delete_question_api_teaching_classes__class_id__preparation_session_questions_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DeleteQuestionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 题目删除失败 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以删除题目 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 题目不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    update_question_api_teaching_classes__class_id__preparation_session_questions__question_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                question_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateQuestionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_QuestionView_"];
                };
            };
            /** @description 题目更新失败 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以更新题目 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 题目不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    confirm_candidate_question_api_teaching_classes__class_id__preparation_session_questions_confirm_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConfirmCandidateQuestionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_QuestionView_"];
                };
            };
            /** @description 候选题确认失败 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以确认候选题 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 题目不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    generate_candidate_questions_api_teaching_classes__class_id__preparation_session_questions_candidates_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CandidateQuestionGenerationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_CandidateQuestionGenerationView_"];
                };
            };
            /** @description 出题重点或题数无效 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以生成候选题 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    publish_preparation_question_api_teaching_classes__class_id__preparation_session_questions__question_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                question_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PublishQuestionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_QuestionPublicationView_"];
                };
            };
            /** @description 题目尚未确认或作业字段非法 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以发布题目 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话或题目不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 该题目已发布此类型内容 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    publish_preparation_session_api_teaching_classes__class_id__preparation_session_publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 发布条件不满足 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以发布备课会话 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话已发布，不能重复发布 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    publish_homework_api_teaching_classes__class_id__preparation_session_publish_homework_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PublishHomeworkRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PublishHomeworkResponse_"];
                };
            };
            /** @description 发布条件不满足或字段非法 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有教师可以发布作业 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课会话已发布，不能重复发布 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    select_preparation_session_documents_api_teaching_classes__class_id__preparation_session_documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SelectPreparationDocumentsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PreparationSessionView_"];
                };
            };
            /** @description 只有教师可以选择备课文档 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课文档或会话不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 备课文档尚未准备好 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_classroom_practice_content_detail_api_teaching_classes__class_id__published_contents__content_id__practice_detail_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ClassroomPracticeContentDetailView_"];
                };
            };
            /** @description 该内容不是课堂练习 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以查看课堂练习 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 课堂练习不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    submit_classroom_practice_answer_api_teaching_classes__class_id__published_contents__content_id__submit_answer_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ClassroomPracticeAnswerBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ClassroomPracticeResultView_"];
                };
            };
            /** @description 已作答或答案无效 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以作答课堂练习 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 课堂练习不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_baseline_practice_detail_api_teaching_classes__class_id__published_contents__content_id__baseline_practice_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_BaselinePracticeDetail_"];
                };
            };
            /** @description 该内容不是基准练习 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以查看基准练习 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 基准练习不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    submit_baseline_practice_answer_api_teaching_classes__class_id__published_contents__content_id__baseline_practice_submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BaselinePracticeSubmitRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_BaselinePracticeResult_"];
                };
            };
            /** @description 答案为空或练习已进入终态 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以提交基准练习 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 基准练习不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    abandon_baseline_practice_api_teaching_classes__class_id__published_contents__content_id__baseline_practice_abandon_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                content_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_BaselinePracticeResult_"];
                };
            };
            /** @description 练习已进入终态 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以放弃基准练习 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 基准练习不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_mastery_summary_api_teaching_classes__class_id__mastery_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_MasterySummaryView_"];
                };
            };
            /** @description 只有班级正式成员可以查看掌握度摘要 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    save_homework_draft_api_teaching_classes__class_id__homework__homework_id__save_draft_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                homework_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveHomeworkDraftBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_HomeworkSubmissionView_"];
                };
            };
            /** @description 作业已提交或答案格式无效 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以保存作业草稿 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 作业不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    submit_homework_api_teaching_classes__class_id__homework__homework_id__submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                homework_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmitHomeworkBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_HomeworkSubmissionResultView_"];
                };
            };
            /** @description 作业已提交或答案格式无效 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 只有班级正式成员可以提交作业 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 作业不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_homework_submission_detail_api_teaching_classes__class_id__homework__homework_id__submission_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                homework_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_HomeworkSubmissionDetailView_"];
                };
            };
            /** @description 只有班级正式成员可以查看作业提交详情 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 作业不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_homework_for_learner_api_teaching_classes__class_id__homework_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_HomeworkListView_"];
                };
            };
            /** @description 只有班级正式成员可以查看作业列表 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_teacher_homework_api_teaching_classes__class_id__teacher_homework_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeacherHomeworkListView_"];
                };
            };
            /** @description 只有班级教师可以查看作业统计 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_webots_pairing_api_teaching_classes__class_id__webots_pairing_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_PairingView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    bind_webots_pairing_api_teaching_classes__class_id__webots_pairing_bind_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PairingBindRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ConnectorView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    report_webots_environment_api_teaching_classes__class_id__webots_environment_post: {
        parameters: {
            query?: never;
            header?: {
                "X-Connector-Token"?: string | null;
            };
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EnvironmentReportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_EnvironmentView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_webots_environment_api_teaching_classes__class_id__webots_environment__connector_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                connector_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_EnvironmentView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_webots_tasks_api_teaching_classes__class_id__webots_tasks_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TaskCatalogView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    list_webots_runs_api_teaching_classes__class_id__webots_runs_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_list_RunView__"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    create_webots_run_api_teaching_classes__class_id__webots_runs_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_RunView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    command_webots_run_api_teaching_classes__class_id__webots_runs__run_id__command_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunCommandRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_RunView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    add_webots_event_api_teaching_classes__class_id__webots_runs__run_id__events_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunEventRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_RunView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    submit_webots_result_api_teaching_classes__class_id__webots_runs__run_id__result_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunResultRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_RunView_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    validate_webots_envelope_api_teaching_classes__class_id__webots_messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProtocolEnvelope"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ProtocolEnvelope_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_class_aggregate_stats_api_teaching_classes__class_id__aggregate_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ClassAggregateStatsView_"];
                };
            };
            /** @description 只有教学班正式成员可以查看聚合统计 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_teacher_dashboard_api_teaching_classes__class_id__teacher_dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeacherDashboardView_"];
                };
            };
            /** @description 只有班级教师可以查看dashboard */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    generate_teacher_ai_analysis_api_teaching_classes__class_id__teacher_dashboard_ai_analysis_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_TeacherAIAnalysisView_"];
                };
            };
            /** @description 只有班级教师可以生成学情分析 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_teacher_simulation_summary_api_teaching_classes__class_id__webots_simulation_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SimulationSummaryView_"];
                };
            };
            /** @description 只有班级教师可以查看仿真摘要 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_class_learners_api_teaching_classes__class_id__learners_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_LearnerListView_"];
                };
            };
            /** @description 只有班级教师可以查看学习者列表 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 教学班不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_learner_detail_api_teaching_classes__class_id__learners__learner_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                learner_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_LearnerDetailView_"];
                };
            };
            /** @description 只有班级教师可以查看学习者详情 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 学习者不存在或不是班级正式成员 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_teacher_learner_simulation_summary_api_teaching_classes__class_id__learners__learner_id__webots_simulation_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                learner_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SimulationSummaryView_"];
                };
            };
            /** @description 只有班级教师可以查看仿真摘要 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 学习者不存在或不是班级正式成员 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    get_homework_ai_analysis_api_teaching_classes__class_id__homework__homework_id__ai_analysis__learner_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: string;
                homework_id: string;
                learner_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_HomeworkAIAnalysisView_"];
                };
            };
            /** @description 只有班级教师可以查看 AI 作业分析 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 作业或学习者不存在 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
    ask_xiaod_api_xiaod_chat_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["XiaodChatRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_XiaodChatView_"];
                };
            };
            /** @description 登录状态已失效 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
            /** @description 请求参数不正确 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_NoneType_"];
                };
            };
        };
    };
}
