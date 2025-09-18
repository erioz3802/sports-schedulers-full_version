# Sports Schedulers - Assignments API
# Author: Jose Ortiz
# Copyright: 2025

from flask import Blueprint, request, jsonify, session
from models import db, Assignment, Game, Official
from utils.decorators import require_login, require_role
from utils.logger import log_activity
from utils.validators import validate_required_fields
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/assignments')

@assignments_bp.route('', methods=['GET'])
@require_login
def get_assignments():
    """Get all assignments with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        game_id = request.args.get('game_id', type=int)
        official_id = request.args.get('official_id', type=int)
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = Assignment.query.join(Game).join(Official)
        
        # Apply filters
        if game_id:
            query = query.filter(Assignment.game_id == game_id)
        if official_id:
            query = query.filter(Assignment.official_id == official_id)
        if status:
            query = query.filter(Assignment.status == status)
        if date_from:
            query = query.filter(Game.date >= date_from)
        if date_to:
            query = query.filter(Game.date <= date_to)
        
        # Order by game date and time
        query = query.order_by(Game.date.desc(), Game.time.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        assignments = []
        for assignment in pagination.items:
            assignments.append({
                'id': assignment.id,
                'game_id': assignment.game_id,
                'official_id': assignment.official_id,
                'position': assignment.position,
                'status': assignment.status,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
                'game': {
                    'date': assignment.game.date,
                    'time': assignment.game.time,
                    'home_team': assignment.game.home_team,
                    'away_team': assignment.game.away_team,
                    'location': assignment.game.location,
                    'sport': assignment.game.sport,
                    'level': assignment.game.level
                },
                'official': {
                    'first_name': assignment.official.first_name,
                    'last_name': assignment.official.last_name,
                    'full_name': f'{assignment.official.first_name} {assignment.official.last_name}',
                    'email': assignment.official.email,
                    'phone': assignment.official.phone
                }
            })
        
        return jsonify({
            'success': True,
            'assignments': assignments,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching assignments: {str(e)}'}), 500

@assignments_bp.route('', methods=['POST'])
@require_role(['super_admin', 'admin', 'assigner'])
def create_assignment():
    """Create a new assignment"""
    try:
        data = request.get_json()
        required_fields = ['game_id', 'official_id', 'position']
        
        # Validate required fields
        missing_fields = validate_required_fields(data, required_fields)
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Verify game exists
        game = Game.query.get(data['game_id'])
        if not game:
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        # Verify official exists and is active
        official = Official.query.get(data['official_id'])
        if not official:
            return jsonify({'success': False, 'message': 'Official not found'}), 404
        if not official.active:
            return jsonify({'success': False, 'message': 'Official is not active'}), 400
        
        # Check for duplicate assignment (same game, same official)
        existing = Assignment.query.filter_by(
            game_id=data['game_id'],
            official_id=data['official_id']
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Official is already assigned to this game'
            }), 400
        
        # Check for conflicting assignments (same time, same official)
        conflicting = Assignment.query.join(Game).filter(
            Assignment.official_id == data['official_id'],
            Game.date == game.date,
            Game.time == game.time,
            Assignment.id != Assignment.id  # Exclude current assignment if updating
        ).first()
        if conflicting:
            return jsonify({
                'success': False,
                'message': f'Official has conflicting assignment at the same time'
            }), 400
        
        # Create new assignment
        assignment = Assignment(
            game_id=data['game_id'],
            official_id=data['official_id'],
            position=data['position'],
            status=data.get('status', 'Assigned'),
            assigned_by=session.get('user_id')
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        # Log activity
        log_activity(
            session.get('user_id'),
            'create',
            'assignment',
            assignment.id,
            f'Assigned {official.first_name} {official.last_name} to {game.home_team} vs {game.away_team} as {assignment.position}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Assignment created successfully',
            'assignment_id': assignment.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating assignment: {str(e)}'}), 500

@assignments_bp.route('/<int:assignment_id>', methods=['GET'])
@require_login
def get_assignment(assignment_id):
    """Get a specific assignment by ID"""
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        
        return jsonify({
            'success': True,
            'assignment': {
                'id': assignment.id,
                'game_id': assignment.game_id,
                'official_id': assignment.official_id,
                'position': assignment.position,
                'status': assignment.status,
                'assigned_by': assignment.assigned_by,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
                'game': {
                    'id': assignment.game.id,
                    'date': assignment.game.date,
                    'time': assignment.game.time,
                    'home_team': assignment.game.home_team,
                    'away_team': assignment.game.away_team,
                    'location': assignment.game.location,
                    'sport': assignment.game.sport,
                    'level': assignment.game.level
                },
                'official': {
                    'id': assignment.official.id,
                    'first_name': assignment.official.first_name,
                    'last_name': assignment.official.last_name,
                    'email': assignment.official.email,
                    'phone': assignment.official.phone,
                    'sport': assignment.official.sport,
                    'level': assignment.official.level
                }
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching assignment: {str(e)}'}), 500

@assignments_bp.route('/<int:assignment_id>', methods=['PUT'])
@require_role(['super_admin', 'admin', 'assigner'])
def update_assignment(assignment_id):
    """Update an existing assignment"""
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'position' in data:
            assignment.position = data['position']
        if 'status' in data:
            assignment.status = data['status']
        if 'official_id' in data:
            # Verify new official exists and is active
            official = Official.query.get(data['official_id'])
            if not official:
                return jsonify({'success': False, 'message': 'Official not found'}), 404
            if not official.active:
                return jsonify({'success': False, 'message': 'Official is not active'}), 400
            
            # Check for duplicate assignment with new official
            existing = Assignment.query.filter_by(
                game_id=assignment.game_id,
                official_id=data['official_id']
            ).filter(Assignment.id != assignment_id).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Official is already assigned to this game'
                }), 400
            
            assignment.official_id = data['official_id']
        
        db.session.commit()
        
        # Log activity
        log_activity(
            session.get('user_id'),
            'update',
            'assignment',
            assignment.id,
            f'Updated assignment for {assignment.game.home_team} vs {assignment.game.away_team}'
        )
        
        return jsonify({'success': True, 'message': 'Assignment updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating assignment: {str(e)}'}), 500

@assignments_bp.route('/<int:assignment_id>', methods=['DELETE'])
@require_role(['super_admin', 'admin', 'assigner'])
def delete_assignment(assignment_id):
    """Delete an assignment"""
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        assignment_info = f'{assignment.official.first_name} {assignment.official.last_name} - {assignment.game.home_team} vs {assignment.game.away_team}'
        
        db.session.delete(assignment)
        db.session.commit()
        
        # Log activity
        log_activity(
            session.get('user_id'),
            'delete',
            'assignment',
            assignment_id,
            f'Deleted assignment: {assignment_info}'
        )
        
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting assignment: {str(e)}'}), 500

@assignments_bp.route('/bulk', methods=['POST'])
@require_role(['super_admin', 'admin', 'assigner'])
def bulk_assign():
    """Create multiple assignments at once"""
    try:
        data = request.get_json()
        assignments_data = data.get('assignments', [])
        
        if not assignments_data:
            return jsonify({'success': False, 'message': 'No assignments provided'}), 400
        
        created_assignments = []
        errors = []
        
        for i, assignment_data in enumerate(assignments_data):
            try:
                # Validate required fields
                required_fields = ['game_id', 'official_id', 'position']
                missing_fields = validate_required_fields(assignment_data, required_fields)
                if missing_fields:
                    errors.append(f'Assignment {i+1}: Missing fields {missing_fields}')
                    continue
                
                # Create assignment
                assignment = Assignment(
                    game_id=assignment_data['game_id'],
                    official_id=assignment_data['official_id'],
                    position=assignment_data['position'],
                    status=assignment_data.get('status', 'Assigned'),
                    assigned_by=session.get('user_id')
                )
                
                db.session.add(assignment)
                created_assignments.append(assignment)
                
            except Exception as e:
                errors.append(f'Assignment {i+1}: {str(e)}')
        
        if created_assignments:
            db.session.commit()
            
            # Log activity
            log_activity(
                session.get('user_id'),
                'bulk_create',
                'assignments',
                None,
                f'Created {len(created_assignments)} assignments'
            )
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created_assignments)} assignments',
            'created_count': len(created_assignments),
            'errors': errors
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error in bulk assignment: {str(e)}'}), 500

@assignments_bp.route('/stats', methods=['GET'])
@require_login
def get_assignments_stats():
    """Get assignments statistics"""
    try:
        total_assignments = Assignment.query.count()
        
        # Assignments by status
        status_stats = db.session.query(
            Assignment.status, db.func.count(Assignment.id)
        ).group_by(Assignment.status).all()
        
        # Assignments by position
        position_stats = db.session.query(
            Assignment.position, db.func.count(Assignment.id)
        ).group_by(Assignment.position).all()
        
        # Recent assignments (last 30 days)
        from datetime import date, timedelta
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_assignments = Assignment.query.join(Game).filter(
            Game.date >= thirty_days_ago.strftime('%Y-%m-%d')
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_assignments': total_assignments,
                'recent_assignments': recent_assignments,
                'by_status': dict(status_stats),
                'by_position': dict(position_stats)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching stats: {str(e)}'}), 500
