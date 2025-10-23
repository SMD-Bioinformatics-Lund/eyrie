# Changelog

All notable changes to the Eyrie sample management system will be documented in this file.

## [Unreleased]

### Added
**License**
 - Added MIT license
 - README uses shields to fetch license and version number

**Apache Proxy Deployment Configuration**
 - Added `environment.prod` file with dual URL configuration for Apache reverse proxy
 - Added `apache-proxy.conf` with complete Apache proxy configuration
 - Created environment-based deployment system with version management
 - Added support for external vs internal URL routing
 - Configured host port mapping for production deployment

**Server-side authentication system**
 - Created Flask authentication decorators (`@login_required`, `@admin_required_view`, `@role_required`)
 - Implemented server-side route protection that cannot be bypassed client-side
 - Added session-based authentication validation for all protected routes
 - Created centralized authentication decorator system in `auth/decorators.py`

**Trends snalysis system**
 - Added comprehensive trends analysis with interactive Plotly charts
 - Implemented trends API endpoint with time-based filtering and grouping options
 - Added multiple metrics analysis: read counts, quality scores, contaminants, top hits
 - Created dedicated trends blueprint with complete frontend implementation

**Server-side admin button visibility**
 - Implemented Jinja template conditionals for admin button rendering
 - Admin buttons only exist in HTML for admin users (cannot be bypassed)
 - Switched from `send_file()` to `render_template()` for dynamic user context
 - Added `current_user` parameter to all templates for role-based rendering

**Enhanced API security**
 - Added `@api_authentication` decorator to all sample data endpoints
 - Protected trends API with authentication requirements
 - Added server-side validation to QC and comment update endpoints
 - Implemented comprehensive API endpoint protection

**Two-column species flagging system**
 - Added unified species flags API endpoint (`PUT /api/samples/{sample_id}/species-flags`) 
 - Added flags persistence in MongoDB with `flagged_contaminants` and `flagged_top_hits` fields
 - Added classification view with two-column flagging: green stars (top hits) and red flags (contaminants)
 - Added comprehensive flagging summary statistics display for both flag types

**Spike species detection system**
 - Added spike species configuration and detection functionality
 - Implemented end-to-end spike detection from parsing to frontend display
 - Added spike species highlighting in Species Abundance table with blue background
 - Added spike species display in Classification Summary cards
 - Added native browser tooltips for spike species identification

**Enhanced species abundance table**
 - Added "Estimated Counts" column and CSV export functionality

**Eyrie-popup modularization**
 - Restructured eyrie-popup codebase into logical modules for improved maintainability
 - Added dynamic version management

### Enhanced
**Security architecture**
 - Replaced client-side authentication with server-side Flask decorators
 - Eliminated JavaScript-based security decisions that could be bypassed
 - Implemented robust session-based authentication with HTTP-only cookies
 - Enhanced API endpoint security with comprehensive authentication requirements

**UI/UX improvements**
 - Improved navbar layout and responsive design
 - Enhanced table layouts and Krona plot responsiveness
 - Disabled automatic chart updates in favor of manual updates

**Infrastructure and networking**
 - Fixed Docker container networking and added Flask proxy routes
 - Enhanced backend connectivity between Flask and FastAPI services

### Fixed
**Critical security vulnerabilities**
 - Eliminated client-side admin page protection that could be bypassed
 - Fixed client-side admin button hiding that could be manipulated
 - Removed JavaScript-based authentication checks in favor of server-side protection
 - Fixed API endpoints missing authentication requirements

**Authentication issues**
 - Fixed logout function across all views and corrected API endpoint calls
 - Resolved duplicate authentication functions

**Infrastructure issues**
 - Fixed Docker container networking and API proxy routing
 - Fixed hardcoded API URLs to use relative paths

**Code quality**
 - Fixed file formatting and removed deprecated functions

### Changed
**Authentication architecture**
 - Replaced client-side authentication with server-side Flask decorators
 - Switched from `send_file()` to `render_template()` for dynamic user context
 - Updated all view templates to receive `current_user` parameter
 - Consolidated authentication logic into centralized decorator system
 - Removed template inheritance attempt in favor of standalone templates with user context

**API security model**
 - All sample API endpoints now require authentication
 - Trends API endpoints require authentication
 - QC and comment update endpoints require authentication
 - Modified species flagging endpoints to use session-based authentication for frontend compatibility
 - Added new trends endpoint with comprehensive filtering and grouping capabilities

**Template rendering**
 - Changed from static file serving to dynamic Jinja template rendering
 - Admin buttons conditionally rendered based on server-side user role
 - User context passed to all templates for role-based UI decisions

**Code organization**
 - Improved code structure with logical separation of concerns
 - Created shared JavaScript directory and reorganized utilities

**Deployment Configuration**
 - Updated `docker-compose.yml` to use environment variables with fallback defaults
 - Added version management for all Docker images including MongoDB
 - Configured dual URL system for Apache proxy deployment
 - Updated README with production deployment instructions

## [0.2.1]

### Added

### Enhanced

### Fixed

 - Fixed `.gitignore` *auth* bug

### Changed

## [0.2.0]

### Added
**Contamination flag management system**
 - Added persistent contamination flagging functionality for taxonomic species
 - Implemented contamination flags API endpoint (`PUT /api/samples/{sample_id}/contamination`)
 - Added contamination flags persistence in MongoDB with `flagged_contaminants` field
 - Enhanced classification view with interactive flag buttons for each species
 - Added contamination summary statistics display (flagged contaminants count)

**Enhanced sample detail navigation**
 - Implemented three-tab navigation system: Overview, Classification, and Nanoplot views
 - Added view-specific data loading and display functionality

**Comprehensive NanoStats integration**
 - Enhanced Summary Statistics to display all 8 processed NanoStats metrics
 - Added proper number formatting and unit display

**Authentication & authorization system**
 - Implemented JWT-based authentication with role-based access control (RBAC)
 - Added user roles: admin, uploader, and user
 - Restricted sample uploading to admin and uploader roles only
 - Added session-based authentication for frontend compatibility
 - Created authentication middleware and decorators

### Enhanced
**File path management**
 - Fixed HTML file rendering and resolved path mismatches between database and web serving

**Data processing & parsing**
 - Updated eyrie-popup parser for correct TSV parsing and improved taxonomic data processing

**User interface improvements**
 - Enhanced quality visualization and improved responsive design
 - Fixed Krona plot sizing and card layouts

### Fixed
**Database & backend issues**
 - Resolved MongoDB ObjectId conversion errors and Docker build issues
 - Added missing dependencies and corrected schema mismatches

**Authentication & session management**
 - Fixed authentication mismatch between backend and frontend
 - Resolved API authentication issues and improved session handling

**Template & file organization**
 - Improved template organization and navigation consistency

### Changed
**API endpoints**
 - Updated endpoints for proper role-based access and enhanced error handling

**Data model updates**
 - Added `flagged_contaminants` field to sample schema
 - Enhanced taxonomic data structure with top species abundance information
 - Updated sample timestamps for contamination flag changes
