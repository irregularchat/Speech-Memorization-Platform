"""
Context processors for adding demo authentication info to all templates
"""

def demo_auth(request):
    """Add demo authentication info to template context"""
    is_demo_authenticated = request.session.get('demo_user', False)
    demo_username = request.session.get('demo_username', 'demo')
    
    return {
        'is_demo_authenticated': is_demo_authenticated,
        'demo_username': demo_username,
        'is_authenticated': request.user.is_authenticated or is_demo_authenticated,
        'current_username': request.user.username if request.user.is_authenticated else demo_username,
    }