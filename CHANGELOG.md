# Changelog

All notable changes to the Eyrie sample management system will be documented in this file.

## [Unreleased]

### Added
**Server-Side Authentication System**
 - Created Flask authentication decorators (`@login_required`, `@admin_required_view`, `@role_required`)
 - Implemented server-side route protection that cannot be bypassed client-side
 - Added session-based authentication validation for all protected routes
 - Created centralized authentication decorator system in `auth/decorators.py`

**Trends Analysis System**
 - Added comprehensive trends analysis with interactive Plotly charts
 - Implemented trends API endpoint (`GET /api/trends/data`) with filtering and grouping
 - Added Flask proxy route to forward trends requests to FastAPI backend
 - Added time-based filtering: 7 days, 30 days, 90 days, 1 year, all time
 - Added grouping options: daily, weekly, monthly aggregation
 - Added multiple metrics analysis: read counts, quality scores, contaminants, top hits
 - Added category-based analysis: tissue sample type, classification type, spike species
 - Added manual chart updates with export functionality
 - Created dedicated trends blueprint with complete frontend implementation
 - Added British English spelling throughout the trends interface

**Server-Side Admin Button Visibility**
 - Implemented Jinja template conditionals for admin button rendering
 - Admin buttons only exist in HTML for admin users (cannot be bypassed)
 - Switched from `send_file()` to `render_template()` for dynamic user context
 - Added `current_user` parameter to all templates for role-based rendering

**Enhanced API Security**
 - Added `@api_authentication` decorator to all sample data endpoints
 - Protected trends API with authentication requirements
 - Added server-side validation to QC and comment update endpoints
 - Implemented comprehensive API endpoint protection

**Two-Column Species Flagging System**
 - Added unified species flags API endpoint (`PUT /api/samples/{sample_id}/species-flags`) 
 - Added flags persistence in MongoDB with `flagged_contaminants` and `flagged_top_hits` fields
 - Added classification view with two-column flagging: green stars (top hits) and red flags (contaminants)
 - Added comprehensive flagging summary statistics display for both flag types

**Spike Species Detection System**
 - Added spike species configuration and detection functionality
 - Implemented end-to-end spike detection from parsing to frontend display
 - Added spike species highlighting in Species Abundance table with blue background
 - Added spike species display in Classification Summary cards
 - Added native browser tooltips for spike species identification

**Enhanced Species Abundance Table**
 - Added "Estimated Counts" column to Species Abundance table
 - Implemented centered alignment for table headers and cells (except Species column)
 - Added CSV export functionality for abundance data

**Eyrie-Popup Modularization**
 - Restructured eyrie-popup codebase into logical modules:
  - Separated parser into specialized modules (nanoplot, nanostats, taxonomic)
  - Split models by purpose (config, data, parsing)
  - Organized API client by functionality (client, upload, format)
  - Created `utils/` directory for reusable utility functions
 - Added dynamic version management with `__version__.py`
 - Updated import structure for improved maintainability

### Enhanced
**Security Architecture**
 - Replaced client-side authentication with server-side Flask decorators
 - Eliminated JavaScript-based security decisions that could be bypassed
 - Implemented robust session-based authentication with HTTP-only cookies
 - Enhanced API endpoint security with comprehensive authentication requirements

**UI/UX Improvements**
 - Left-aligned navbar navigation buttons with right-aligned user dropdown
 - Disabled automatic chart updates in favor of manual "Update Chart" button
 - Removed distracting chart footer text for cleaner visualization
 - Fixed navbar positioning and responsive layout across all views
 - Improved Species Abundance table layout (col-lg-6 for better width)
 - Made Krona plot responsive with viewport height (85vh)
 - Enhanced table styling with centered content alignment

**Infrastructure and Networking**
 - Fixed Docker container networking for trends API communication
 - Added Flask proxy routes for seamless frontend-backend integration
 - Improved URL routing with clean `/trends` endpoint (no trailing slash)
 - Enhanced backend connectivity between Flask and FastAPI services

**Data Flow**
 - Updated backend API format conversion to include estimated_counts field
 - Improved spike detection integration across parsing, backend, and frontend
 - Enhanced trends data aggregation with comprehensive filtering options

### Fixed
**Critical Security Vulnerabilities**
 - Eliminated client-side admin page protection that could be bypassed
 - Fixed client-side admin button hiding that could be manipulated
 - Removed JavaScript-based authentication checks in favor of server-side protection
 - Fixed API endpoints missing authentication requirements

**Authentication Issues**
 - Fixed logout function not working in sample detail, classification, and nanoplot views
 - Resolved duplicate authentication functions across multiple blueprints
 - Fixed incorrect logout API endpoint calls (was `/logout`, now `/api/auth/logout`)
 - Added missing shared.js imports to sample view templates

**Infrastructure Issues**
 - Fixed Docker container networking (changed `eyrie-backend` to `eyrie_backend`)
 - Fixed trends chart not rendering due to missing API proxy route
 - Fixed trends URL ending with unnecessary trailing slash
 - Fixed hardcoded API URLs to use relative paths

**Code Quality**
 - Added missing newlines to all source files for POSIX compliance
 - Fixed inconsistent file formatting across Python, JavaScript, and HTML files
 - Removed deprecated `requireAuthentication()` function

**Backend Models**
 - Added spike field support to SampleCreate and SampleUpdate models
 - Updated MongoDB initialization scripts for spike field support

### Changed
**Authentication Architecture**
 - Replaced client-side authentication with server-side Flask decorators
 - Switched from `send_file()` to `render_template()` for dynamic user context
 - Updated all view templates to receive `current_user` parameter
 - Consolidated authentication logic into centralized decorator system
 - Removed template inheritance attempt in favor of standalone templates with user context

**API Security Model**
 - All sample API endpoints now require authentication
 - Trends API endpoints require authentication
 - QC and comment update endpoints require authentication
 - Modified species flagging endpoints to use session-based authentication for frontend compatibility
 - Added new trends endpoint with comprehensive filtering and grouping capabilities

**Template Rendering**
 - Changed from static file serving to dynamic Jinja template rendering
 - Admin buttons conditionally rendered based on server-side user role
 - User context passed to all templates for role-based UI decisions

**Data Model Updates**
 - Added `flagged_contaminants` and `flagged_top_hits` fields to sample schema
 - Updated sample timestamps for species flag changes

**Layout Adjustments**
 - Changed Krona plot from col-lg-8 to col-lg-6 (narrower)
 - Changed Species Abundance table from col-lg-4 to col-lg-6 (wider)
 - Updated Krona plot height to use responsive viewport units (85vh)

**Code Organization**
 - Created shared JavaScript directory (`frontend/eyrie_app/shared/static/js/`)
 - Moved spike detection utilities from config.py to utils/spike_detection.py
 - Simplified config.py to contain only static configuration variables
 - Improved code structure with logical separation of concerns
 - Removed failed template inheritance files (`base.html`)

## [0.2.1]

### Added

### Enhanced

### Fixed

 - Fixed `.gitignore` *auth* bug

### Changed

## [0.2.0]

### Added
**Contamination Flag Management System**
 - Added persistent contamination flagging functionality for taxonomic species
 - Implemented contamination flags API endpoint (`PUT /api/samples/{sample_id}/contamination`)
 - Added contamination flags persistence in MongoDB with `flagged_contaminants` field
 - Enhanced classification view with interactive flag buttons for each species
 - Added contamination summary statistics display (flagged contaminants count)

**Enhanced Sample Detail Navigation**
 - Implemented three-tab navigation system for sample detail view:
  - Overview tab with quality plots and summary statistics
  - Classification tab with Krona plots and taxonomic data
  - Nanoplot tab with detailed sequencing quality visualizations
 - Added view-specific data loading and display functionality

**Comprehensive NanoStats Integration**
 - Enhanced Summary Statistics to display all 8 processed NanoStats from "General summary":
  - Number of Reads
  - Mean Read Length  
  - Mean Read Quality
  - Median Read Length
  - Median Read Quality
  - Read Length N50
  - STDEV Read Length
  - Total Bases
 - Prioritized processed NanoStats over unprocessed data for accuracy
 - Added proper number formatting and unit display (bp, Gb, Mb, Kb, Q scores)

**Authentication & Authorization System**
 - Implemented JWT-based authentication with role-based access control (RBAC)
 - Added user roles: admin, uploader, and user
 - Restricted sample uploading to admin and uploader roles only
 - Added session-based authentication for frontend compatibility
 - Created authentication middleware and decorators

### Enhanced
**File Path Management**
 - Fixed HTML file rendering by correcting file paths with "test/" prefix
 - Updated eyrie-popup to prepend correct path prefixes for web serving
 - Resolved file path mismatches between database storage and web serving

**Data Processing & Parsing**
 - Updated eyrie-popup parser to correctly parse TSV files for relative abundance data
 - Fixed NanoStats regex patterns and TSV delimiter handling
 - Improved taxonomic data parsing to filter unmapped entries
 - Enhanced abundance data conversion and processing

**User Interface Improvements**
 - Used NanoPlot LengthvsQualityScatterPlot for quality visualization in Overview tab
 - Fixed Krona plot sizing to properly fill classification view card
 - Removed pipeline files card from sample view (no longer needed)
 - Enhanced responsive design and card layouts

### Fixed
**Database & Backend Issues**
 - Resolved MongoDB ObjectId conversion errors in JWT authentication
 - Fixed Docker build context issues with new authentication files
 - Added missing PyJWT dependency to backend container
 - Corrected database schema mismatches for contamination data

**Authentication & Session Management**
 - Fixed authentication mismatch between JWT-based backend and session-based frontend
 - Resolved contamination flag API authentication issues
 - Added proper session cookie handling for frontend API calls

**Template & File Organization**
 - Renamed sample detail template from `detail.html` to `sample.html` for consistency
 - Fixed navigation tab placement (sample detail view only, not samples list)
 - Corrected template routing and view rendering

### Changed
**API Endpoints**
 - Updated sample endpoints to require admin/uploader roles for modifications
 - Modified contamination endpoint to use session-based authentication for frontend compatibility
 - Enhanced error handling and response formatting across all endpoints

**Data Model Updates**
 - Added `flagged_contaminants` field to sample schema
 - Enhanced taxonomic data structure with top species abundance information
 - Updated sample timestamps for contamination flag changes

**Development & Deployment**
 - Updated Docker containerization with manual file copying for development
 - Enhanced container restart procedures for applying code changes
 - Improved logging and debugging capabilities
