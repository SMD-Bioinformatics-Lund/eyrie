# Changelog

All notable changes to the Eyrie sample management system will be documented in this file.

## [Unreleased]

### Added
 - Implemented QC (array with timestamps/users) and general (string) comments with separate submission buttons
 - Added display sample metadata fields (sample_type, tissue, dilution, etc.)
 - Added ability to upload sample metadata via eyrie-popup tool
 - Added `/api/system/health` endpoint for proper application health checking

### Fixed
 - Fixed MongoDB connection issues by removing root authentication requirements
 - Fixed misleading success messages in eyrie-popup when uploads actually fail

### Changed
 - Reorganized three-column layout with metadata card and centered visualizations
 - Changed db to hierarchical organization (nested file paths)
 - Removed authentication barriers for direct database access without requiring `db.auth()`
 - Unified upload command in eyrie-popup supporting both sample data and metadata
 - Improved eyrie-popup upload command with accurate status messaging
 - Comprehensive removal of unnecessary comments across entire codebase
 - Updated Docker Compose configuration to support both pre-built images and local development builds
 - Changed Docker builds to python v11.3.0

## [0.3.0]

### Added
 - Added MIT license
 - README uses shields to fetch license and version number
 - Added `environment.prod` file with dual URL configuration for Apache reverse proxy
 - Added `apache-proxy.conf` with complete Apache proxy configuration
 - Created environment-based deployment system with version management
 - Added support for external vs internal URL routing
 - Configured host port mapping for production deployment
 - Created Flask authentication decorators (`@login_required`, `@admin_required_view`, `@role_required`)
 - Implemented server-side route protection that cannot be bypassed client-side
 - Added session-based authentication validation for all protected routes
 - Created centralized authentication decorator system in `auth/decorators.py`
 - Added comprehensive trends analysis with interactive Plotly charts
 - Implemented trends API endpoint with time-based filtering and grouping options
 - Added multiple metrics analysis for trends: read counts, quality scores, contaminants, top hits
 - Created dedicated trends blueprint with complete frontend implementation
 - Implemented Jinja template conditionals for admin button rendering
 - Admin buttons only exist in HTML for admin users (cannot be bypassed)
 - Switched from `send_file()` to `render_template()` for dynamic user context
 - Added `current_user` parameter to all templates for role-based rendering
 - Added `@api_authentication` decorator to all sample data endpoints
 - Protected trends API with authentication requirements
 - Added server-side validation to QC and comment update endpoints
 - Implemented comprehensive API endpoint protection
 - Added classification view with two-column flagging: green stars (top hits) and red flags (contaminants)
 - Added unified species flags API endpoint (`PUT /api/samples/{sample_id}/species-flags`) 
 - Added flags persistence in MongoDB with `flagged_contaminants` and `flagged_top_hits` fields
 - Added comprehensive flagging summary statistics display for both flag types
 - Added spike species configuration and detection functionality
 - Implemented end-to-end spike detection from parsing to frontend display
 - Added spike species highlighting in Species Abundance table with blue background
 - Added spike species display in Classification Summary cards
 - Added "Estimated Counts" column and CSV export functionality
 - Created reusable Jinja2 macros for consistent sample view rendering
 - Added dynamic navigation with shared navbar component
 - Converted database operations from synchronous PyMongo to async Motor driver
 - Implemented lazy database initialization for improved performance
 - Added async support throughout the backend API for better scalability
 - Added environment-aware URL construction to replace hardcoded base paths
 - Implemented dynamic URL generation system for subdirectory deployments
 - Added support for flexible base path configuration
 - Added multi-platform Docker build support for production deployment flexibility
 - Implemented explicit Docker networks for reliable service connectivity
 - Enhanced Docker configuration management and stability
 - Replaced hardcoded API version strings with dynamic imports from `__version__.py` files
 - Restructured eyrie-popup codebase into logical modules for improved maintainability
 - Added new trends endpoint with comprehensive filtering and grouping capabilities
 - Added version management for all Docker images including MongoDB

### Fixed
 - Fixed client-side admin button hiding that could be manipulated
 - Removed JavaScript-based authentication checks in favor of server-side protection
 - Fixed API endpoints missing authentication requirements
 - Fixed logout function across all views and corrected API endpoint calls
 - Fixed Docker container networking and API proxy routing
 - Fixed hardcoded API URLs to use relative paths
 - Removed debug print statements that exposed session data in frontend logs
 - Fixed eyrie-popup file path prepending logic to only use run_directory when provided
 - Resolved Apache compatibility issues by changing data file routes from `/data` to `/analysis-files`
 - Fixed HTML file serving and path mismatches between database and web serving
 - Fixed file formatting and removed deprecated functions

### Changed
 - Eliminated JavaScript-based security decisions that could be bypassed
 - Implemented robust session-based authentication with HTTP-only cookies
 - Enhanced API endpoint security with comprehensive authentication requirements
 - Improved navbar layout and responsive design
 - Enhanced table layouts and Krona plot responsiveness
 - Disabled automatic chart updates in favor of manual updates
 - Converted frontend to API proxy architecture for improved service communication
 - Replaced JavaScript table rendering with server-side Flask/Jinja template rendering
 - Implemented server-side template rendering for better performance and security
 - Removed unused JavaScript files and components
 - Replaced client-side authentication with server-side Flask decorators
 - Removed template inheritance attempt in favor of standalone templates with user context
 - Changed all sample API endpoints to require authentication
 - Modified species flagging endpoints to use session-based authentication for frontend compatibility
 - Changed from static file serving to dynamic Jinja template rendering
 - Admin buttons conditionally rendered based on server-side user role
 - User context passed to all templates for role-based UI decisions
 - Created shared JavaScript directory and reorganized utilities
 - Migrated frontend to API proxy architecture pattern
 - Restructured sample view routing with unified navigation system
 - Removed standalone classification and nanoplot blueprints in favor of integrated sample views
 - Changed data file mount paths from /data to /analysis-files for Apache security compatibility
 - Updated Docker volumes and Flask functions to use consistent /analysis-files naming
 - Switched data file serving from direct static access to authenticated endpoint routing
 - Updated `docker-compose.yml` to use environment variables with fallback defaults
 - Configured dual URL system for Apache proxy deployment
 - Updated README with production deployment instructions
 - Enhanced environment configuration system and Docker setup
 - Enhanced file path handling and upload parsing flexibility
 - Moved authenticated data file serving to proper blueprint with authentication decorators

## [0.2.1]

### Added

### Enhanced

### Fixed

 - Fixed `.gitignore` *auth* bug

### Changed

## [0.2.0]

### Added
 - Added persistent contamination flagging functionality for taxonomic species
 - Implemented contamination flags API endpoint (`PUT /api/samples/{sample_id}/contamination`)
 - Added contamination flags persistence in MongoDB with `flagged_contaminants` field
 - Added interactive flag buttons for each species
 - Added contamination summary statistics display (flagged contaminants count)
 - Implemented three-tab navigation system: Overview, Classification, and Nanoplot views
 - Added view-specific data loading and display functionality
 - Added display of all 8 processed NanoStats metrics
 - Added proper number formatting and unit display
 - Implemented JWT-based authentication with role-based access control (RBAC)
 - Added user roles: admin, uploader, and user
 - Restricted sample uploading to admin and uploader roles only
 - Added session-based authentication for frontend compatibility
 - Created authentication middleware and decorators
 - Added `flagged_contaminants` field to sample schema

### Fixed
 - Resolved MongoDB ObjectId conversion errors and Docker build issues
 - Added missing dependencies and corrected schema mismatches
 - Fixed authentication mismatch between backend and frontend
 - Resolved API authentication issues and improved session handling
 - Fixed HTML file rendering and resolved path mismatches between database and web serving

### Changed
 - Updated eyrie-popup parser for correct TSV parsing and improved taxonomic data processing
 - Changed Krona plot sizing and card layouts
 - Updated endpoints for proper role-based access and enhanced error handling
 - Changed taxonomic data structure with top species abundance information
 - Updated sample timestamps for contamination flag changes
