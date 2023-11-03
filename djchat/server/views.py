from django.shortcuts import render
from rest_framework import viewsets
from .serializer import ServerSerializer
from .models import Server
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.db.models import Count
from .schema import server_list_docs

class ServerListViewSet(viewsets.ViewSet):
    
    queryset = Server.objects.all()
    
    @server_list_docs
    def list(self, request):
        """
        View function to retrieve a list of servers based on query parameters.

        Parameters:
            request (Request): The HTTP request object containing query parameters.

        Query Parameters:
            category (str, optional): Filter servers by category name. If provided, only servers belonging
                                    to the specified category will be included in the response.

            qty (int, optional): Limit the number of servers to be returned. If provided, the response will
                                contain at most 'qty' servers. If not provided or set to None, all matching
                                servers will be returned.

            by_user (bool, optional): Filter servers owned by the requesting user. If set to "true", only servers
                                    created by the authenticated user will be included in the response. Requires
                                    authentication (logged-in user). Default is False.

            by_serverid (int, optional): Filter servers by their unique server ID. If provided, only the server with
                                        the matching ID will be included in the response.

            with_num_members (bool, optional): Include the number of members in each server in the response. If set
                                            to "true", an additional 'num_members' field will be added to each
                                            server object, representing the total number of members in the server.
                                            Default is False.

        Returns:
            Response: JSON response containing a list of servers matching the query parameters.

        Raises:
            AuthenticationFailed: If the 'by_user' or 'by_serverid' query parameter is provided without authentication.
                                This exception will be raised when 'by_user' is set to "true" and the user is not logged in,
                                or when 'by_serverid' is provided without authentication.

            ValidationError: If 'by_serverid' is provided, but the server with the given ID does not exist.
                            This exception will be raised if the 'by_serverid' value is not associated with any server.
                            Also, if the 'by_serverid' value is not a valid integer, a ValidationError will be raised.

        Note:
            - The 'by_user' parameter is only applicable to authenticated users. If used by an anonymous user (not logged in),
            it will raise an AuthenticationFailed exception.

            - The 'with_num_members' parameter can be resource-intensive if the server has a large number of members.
            Use it with caution, especially when dealing with servers containing thousands of members.
    """
        
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"
        
        if category:
            self.queryset = self.queryset.filter(category__name = category)
            
        if by_user and request.user.is_authenticated:
            user_id = request.user.id
            self.queryset = self.queryset.filter(member = user_id)  
        else:
            raise AuthenticationFailed()
            
        if with_num_members:
            self.queryset = self.queryset.annotate(num_members = Count("member")) 
        
        if qty:
            self.queryset = self.queryset[: int(qty)]
        
        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()
            
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server with id {by_serverid} no found")
            except ValueError:
                raise ValidationError(detail=f"Server value error")
        
        
        serializer = ServerSerializer(self.queryset, many=True, context={"num_members":with_num_members})
        return Response(serializer.data)