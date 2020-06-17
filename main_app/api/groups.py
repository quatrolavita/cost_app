from . import api
from flask import jsonify, request, current_app, url_for, g
from ..models import User, Costs, Groups, CostGroup, Permission, Needs
from flask_login import current_user, login_required
from main_app import db
from .errors import forbidden
from ..decorators import permission_required


@api.route('/get_group/<int:id>')
def get_group(id):

    group = Groups.query.get_or_404(id)

    return jsonify(group.to_json()), 200


@api.route('/user_groups')
def get_user_groups():

    user_id = request.args.get('id')
    if user_id is None:
        user_id = g.current_user.id

    interim_req = CostGroup.query.filter_by(user_id=user_id).all()
    result_query = None

    for i in interim_req:
        user_group = db.session.query(Groups).filter_by(id=i.group_id)
        if result_query is None:
            result_query = user_group
        else:
            result_query = result_query.union(user_group)
    if result_query is not None:
        return jsonify({'user_groups': [group.to_json() for group in result_query]}), 200
    return jsonify({'massage': 'user is not in groups jet'})


@api.route('/groups/create', methods=['POST'])
@permission_required(Permission.MODERATE)
def create_group():

    group = Groups.from_json(request.json)

    db.session.add(group)
    db.session.commit()

    return jsonify(group.to_json()), 201


@api.route('/groups/membership', methods=['POST'])
@permission_required(Permission.MODERATE)
def membership():

    user_membership = CostGroup.from_json(request.json)

    db.session.add(user_membership)
    db.session.commit()

    return jsonify(user_membership.to_json()), 201


@api.route('/groups/delete/<int:id>', methods=['DELETE'])
@permission_required(Permission.ADMIN)
def delete_group(id):

    deleted_group = Groups.query.get_or_404(id)
    deleted_costs = Costs.query.filter_by(group_id=id).all()
    deleted_group_mem = CostGroup.query.filter_by(group_id=id).all()
    deleted_needs = Needs.query.filter_by(group_id=id).all()

    for cost in deleted_costs:
        db.session.delete(cost)
        db.session.commit()

    for need in deleted_needs:
        db.session.delete(need)
        db.session.commit()

    for mem in deleted_group_mem:
        db.session.delete(mem)
        db.session.commit()

    db.session.delete(deleted_group)
    db.session.commit()

    return jsonify({'massage': 'Removal was successful'}), 200


@api.route('/groups/delete/membership', methods=['DELETE'])
@permission_required(Permission.MODERATE)
def delete_membership():

    group_members = CostGroup.query.filter_by(
        group_id=request.json.get('group_id')).all()

    deleted_meber = CostGroup.query.filter_by(
        user_id=request.json.get('user_id')).first_or_404()

    db.session.delete(deleted_meber)
    db.session.commit()

    return jsonify({'massage': 'Removal was successful'}), 200


@api.route('/group/update/<int:id>', methods=['PUT'])
@permission_required(Permission.MODERATE)
def update_group(id):

    group = Groups.query.get_or_404(id)

    group.name = request.json.get('name')

    db.session.commit()

    return jsonify(group.to_json()), 200