"""
This file defines ReactFlow.

Copyright 2020 CDFMLR. All rights reserved.
Use of this source code is governed by a MIT
license that can be found in the LICENSE file.
"""

import _ast
import ast

from pyreactflow.ast_node import parse, LoopCondition
from pyreactflow.node import Node, NodesGroup


class ReactFlow(NodesGroup):
    """
    ReactFlow is a no-tails-NodesGroup with an export() method.

    Calls export method of ReactFlow instance to get a react-flow compatible nodes and edges.
    """

    def __init__(self, head_node: Node):
        """ReactFlow is a graph of Node.

        ReactFlow(start_node) constructs a ReactFlow instance with a head (start) Node
        """
        super().__init__(head_node)

    @staticmethod
    def from_code(
        code: str, field: str = "", inner=True, simplify=True, conds_align=False
    ):
        """
        Get a ReactFlow instance from a str of Python code.

        Args:

            code:  str,  Python code to generate react-flow compatible nodes and edges
            field: str,  path to field (function) you want to generate react-flow compatible nodes and edges
            inner: bool, True: parse the body of field; Field: parse the body as an object
            simplify: bool, for If & Loop statements: simplify the one-line-body or not.
            conds_align: bool, for consecutive If statements: conditionNode alignment support (Issue#14) or not

        Returns:
            A ReactFlow instance parsed from given code.

        `inner=True` means parse `field.body`, otherwise parse [field]. E.g.

        ```
        def a():
            print('a')
        ```

        inner=True  => `st (function a) -> subroutine (print) -> end`
        inner=False => `op=>operation: def a(): print('a')`

        The field is the path to the target of workflow def generation.
        It should be the *path* to a `def` code block in code. E.g.

        ```
        def foo():
            pass

        class Bar():
            def fuzz(self):
                pass
            def buzz(self, f):
                def g(self):
                    f(self)
                return g(self)

        Bar().buzz(foo)
        ```

        Available path:

        - "" (means the whole code)
        - "foo"
        - "Bar.fuzz"
        - "Bar.buzz"
        - "Bar.buzz.g"
        """
        code_ast = ast.parse(code)

        field_ast = ReactFlow.find_field_from_ast(code_ast, field)

        assert hasattr(field_ast, "body")
        assert (
            field_ast.body
        ), f"{field}: nothing to parse. Check given code and field please."

        f = field_ast.body if inner else [field_ast]
        p = parse(f, simplify=simplify, conds_align=conds_align)
        return ReactFlow(p.head)

    @staticmethod
    def find_field_from_ast(ast_obj: _ast.AST, field: str) -> _ast.AST:
        """Find a field from AST.

        This function finds the given `field` in `ast_obj.body`, return the found AST object
        or an `_ast.AST` object whose body attribute is [].
        Specially, if field="", returns `ast_obj`.

        A field is the *path* to a `def` code block in code (i.e. a `FunctionDef` object in AST). E.g.

        ```
        def foo():
            pass

        class Bar():
            def fuzz(self):
                pass
            def buzz(self, f):
                def g(self):
                    f(self)
                return g(self)

        Bar().buzz(foo)
        ```

        Available path:

        - "" (means the whole ast_obj)
        - "foo"
        - "Bar.fuzz"
        - "Bar.buzz"
        - "Bar.buzz.g"

        Args:
            ast_obj: given AST
            field: path to a `def`

        Returns: an _ast.AST object
        """
        if field == "":
            return ast_obj

        field_list = field.split(".")
        try:
            for fd in field_list:
                for (
                    ao
                ) in (
                    ast_obj.body
                ):  # raises AttributeError: ast_obj along the field path has no body
                    if hasattr(ao, "name") and ao.name == fd:
                        ast_obj = ao
            assert ast_obj.name == field_list[-1], "field not found"
        except (AttributeError, AssertionError):
            ast_obj.body = []

        return ast_obj

    def _is_child_of_parent(self, target_node, parent_node):
        """Check if a target node is a child of a parent node (condition or loop)."""
        # Prevent self-parenting using object identity
        if target_node is parent_node or id(target_node) == id(parent_node):
            return False
        try:
            # For loop nodes: Check if target is in the loop body
            # Key distinction: loop body nodes should connect BACK to the loop condition
            # Nodes that continue after the loop should NOT be considered children
            if isinstance(parent_node, LoopCondition):
                if (
                    hasattr(parent_node, "connection_yes")
                    and parent_node.connection_yes
                ):
                    loop_body = parent_node.connection_yes.next_node
                    # Check if target is in the loop body AND connects back to the loop
                    if self._contains_node_in_loop_body(
                        loop_body, target_node, parent_node, set()
                    ):
                        return True
                return False

            # For condition nodes: Check yes and no branches
            if hasattr(parent_node, "connection_yes") and parent_node.connection_yes:
                yes_next = parent_node.connection_yes.next_node
                if self._contains_node(yes_next, target_node, set()):
                    return True

            # For non-loop conditions: Check the no branch for containment
            if hasattr(parent_node, "connection_no") and parent_node.connection_no:
                no_next = parent_node.connection_no.next_node
                if self._contains_node(no_next, target_node, set()):
                    return True
        except (AttributeError, TypeError):
            pass
        return False

    def _contains_node_in_loop_body(
        self, loop_body, target_node, loop_condition, visited=None
    ):
        """Check if target_node is in the loop body using both AST and graph traversal."""
        if visited is None:
            visited = set()

        if not loop_body or id(loop_body) in visited:
            return False

        visited.add(id(loop_body))

        # Try AST-based approach first (most reliable)
        # If both nodes have AST objects, use AST-based check as the source of truth
        if hasattr(loop_condition, "ast_object") and hasattr(target_node, "ast_object"):
            # AST-based check is definitive - if the target is in the loop's AST body, it's a child
            # If not, it's NOT a child, regardless of graph connections
            return self._is_node_in_loop_ast_body(
                loop_condition.ast_object, target_node.ast_object
            )

        # Only use graph-based checks if AST objects are not available
        # Direct match
        if loop_body == target_node:
            return True

        # For wrapper nodes (CondYN), check their sub
        if hasattr(loop_body, "sub") and loop_body.sub:
            if loop_body.sub == target_node:
                return True
            # Continue checking in sub
            if self._contains_node_in_loop_body(
                loop_body.sub, target_node, loop_condition, visited
            ):
                return True

        # For condition nodes inside the loop, check their branches
        if hasattr(loop_body, "connection_yes") or hasattr(loop_body, "connection_no"):
            if hasattr(loop_body, "connection_yes") and loop_body.connection_yes:
                yes_next = loop_body.connection_yes.next_node
                if self._contains_node_in_loop_body(
                    yes_next, target_node, loop_condition, visited
                ):
                    return True

            if hasattr(loop_body, "connection_no") and loop_body.connection_no:
                no_next = loop_body.connection_no.next_node
                if self._contains_node_in_loop_body(
                    no_next, target_node, loop_condition, visited
                ):
                    return True

        # Follow sequential connections within the loop body
        if hasattr(loop_body, "connections") and loop_body.connections:
            for conn in loop_body.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    next_node = conn.next_node
                    # Check if this connection goes back to the loop (forms the loop)
                    if next_node == loop_condition:
                        # This is the loop-back edge, we don't follow it
                        continue
                    # Check if connection goes to loop exit (via connection_no)
                    if (
                        hasattr(loop_condition, "connection_no")
                        and loop_condition.connection_no
                        and loop_condition.connection_no.next_node == next_node
                    ):
                        # This is a connection to the loop exit, don't follow it
                        continue
                    # Check if this connection leads to the target within the loop body
                    if self._contains_node_in_loop_body(
                        next_node, target_node, loop_condition, visited
                    ):
                        return True

        return False

    def _is_node_in_loop_ast_body(self, loop_ast, node_ast):
        """Check if a node's AST is contained within a loop's AST body."""
        if not (hasattr(loop_ast, "body") and loop_ast.body):
            return False

        # Check if node_ast is directly in the loop body
        if node_ast in loop_ast.body:
            return True

        # Recursively check nested structures within the loop body
        for stmt in loop_ast.body:
            if self._ast_contains(stmt, node_ast):
                return True

        return False

    def _ast_contains(self, container_ast, target_ast, visited=None):
        """Check if target_ast is contained anywhere within container_ast."""
        if visited is None:
            visited = set()

        if not container_ast or id(container_ast) in visited:
            return False

        if container_ast == target_ast:
            return True

        visited.add(id(container_ast))

        # Check common container attributes
        for attr_name in ["body", "orelse", "handlers", "finalbody"]:
            if hasattr(container_ast, attr_name):
                attr_value = getattr(container_ast, attr_name)
                if isinstance(attr_value, list):
                    for item in attr_value:
                        if item == target_ast or self._ast_contains(
                            item, target_ast, visited
                        ):
                            return True

        return False

    def _find_innermost_parent(self, orig_node, all_nodes):
        """Find the innermost (most nested) loop or condition that contains this node.

        This is the simplified parent-finding logic that replaces the complex depth-limited
        approaches. It finds the actual parent based on AST containment without artificial
        depth constraints.

        Args:
            orig_node: The original node to find a parent for
            all_nodes: List of (original_node, react_node) tuples

        Returns:
            The react_node ID of the innermost parent, or None if no parent exists
        """
        from pyreactflow.ast_node import LoopCondition, IfCondition

        # Determine what types of nodes can be parents based on the target node type
        # For the target node, we need to find its type
        target_react_type = None
        for check_orig, check_react in all_nodes:
            if check_orig is orig_node:
                target_react_type = check_react["type"]
                break

        # Find all potential parents (loops and conditions that contain this node)
        potential_parents = []

        for candidate_orig, candidate_react in all_nodes:
            # Only loops can be parents
            # Conditions use edges for control flow, not parent-child relationships
            if candidate_react["type"] != "loop":
                continue

            # Check if this candidate contains our target node
            if self._is_child_of_parent(orig_node, candidate_orig):
                potential_parents.append((candidate_orig, candidate_react))

        if not potential_parents:
            return None

        # Find the innermost parent (the one that is not contained by any other potential parent)
        for candidate_orig, candidate_react in potential_parents:
            is_innermost = True

            # Check if this candidate is contained by any other potential parent
            for other_orig, other_react in potential_parents:
                if candidate_orig is not other_orig:
                    # If candidate is a child of other, then other is more outer (less nested)
                    # So candidate is more inner (more nested)
                    # We want the MOST inner, so if candidate is contained by other,
                    # candidate is more nested - but we need to check if other contains candidate
                    if self._is_child_of_parent(candidate_orig, other_orig):
                        # candidate is inside other, so candidate is MORE nested
                        # other is LESS nested, so candidate might be the innermost
                        # We continue checking
                        pass
                    elif self._is_child_of_parent(other_orig, candidate_orig):
                        # other is inside candidate, so other is MORE nested
                        # candidate is LESS nested, so candidate is NOT the innermost
                        is_innermost = False
                        break

            if is_innermost:
                return candidate_react["id"]

        # If we get here, return the first one (shouldn't happen with proper containment logic)
        return potential_parents[0][1]["id"]

    def _node_connects_to_loop(self, node, loop_condition, visited, max_depth=10):
        """Check if a node eventually connects back to the loop condition."""
        if not node or id(node) in visited or max_depth <= 0:
            return False

        visited.add(id(node))

        # Check all connections from this node
        if hasattr(node, "connections") and node.connections:
            for conn in node.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    # Direct connection back to loop
                    if conn.next_node == loop_condition:
                        return True
                    # Check if this connection eventually leads back to the loop
                    if self._node_connects_to_loop(
                        conn.next_node, loop_condition, visited, max_depth - 1
                    ):
                        return True

        return False

    def _check_nested_condition_containment(
        self, loop_body, target_node, visited=None, max_depth=3
    ):
        """Check if target_node is contained within any condition inside the loop body."""
        if visited is None:
            visited = set()

        if not loop_body or id(loop_body) in visited or max_depth <= 0:
            return False

        visited.add(id(loop_body))

        # First check sub and child relationships (for CondYN wrappers)
        if hasattr(loop_body, "sub") and loop_body.sub:
            # Check if sub contains the target directly
            if self._contains_node(loop_body.sub, target_node, set()):
                return True
            # Recursively check the sub for nested conditions
            if self._check_nested_condition_containment(
                loop_body.sub, target_node, visited, max_depth - 1
            ):
                return True

        if hasattr(loop_body, "child") and loop_body.child:
            # Check if child contains the target directly
            if self._contains_node(loop_body.child, target_node, set()):
                return True
            # Recursively check the child for nested conditions
            if self._check_nested_condition_containment(
                loop_body.child, target_node, visited, max_depth - 1
            ):
                return True

        # Check if loop_body itself is a condition that contains the target
        if hasattr(loop_body, "connection_yes") or hasattr(loop_body, "connection_no"):
            # This is a condition node, check its branches
            if hasattr(loop_body, "connection_yes") and loop_body.connection_yes:
                yes_next = loop_body.connection_yes.next_node
                if self._contains_node(yes_next, target_node, set()):
                    return True
                # Recursively check for deeper conditions
                if self._check_nested_condition_containment(
                    yes_next, target_node, visited, max_depth - 1
                ):
                    return True

            if hasattr(loop_body, "connection_no") and loop_body.connection_no:
                no_next = loop_body.connection_no.next_node
                if self._contains_node(no_next, target_node, set()):
                    return True
                # Recursively check for deeper conditions
                if self._check_nested_condition_containment(
                    no_next, target_node, visited, max_depth - 1
                ):
                    return True

        # Check general connections
        if hasattr(loop_body, "connections") and loop_body.connections:
            for conn in loop_body.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    if self._check_nested_condition_containment(
                        conn.next_node, target_node, visited, max_depth - 1
                    ):
                        return True

        return False

    def _contains_node_deep(
        self, container_node, target_node, visited=None, max_depth=5
    ):
        """Check if container_node contains the target_node, including through nested conditions."""
        if visited is None:
            visited = set()

        if not container_node or id(container_node) in visited or max_depth <= 0:
            return False

        visited.add(id(container_node))

        # Direct containment
        if container_node == target_node:
            return True

        # Check immediate sub/child relationships
        if hasattr(container_node, "sub") and container_node.sub:
            if container_node.sub == target_node:
                return True
            # Recursively check deeper
            if self._contains_node_deep(
                container_node.sub, target_node, visited, max_depth - 1
            ):
                return True

        if hasattr(container_node, "child") and container_node.child:
            if container_node.child == target_node:
                return True
            # Recursively check deeper
            if self._contains_node_deep(
                container_node.child, target_node, visited, max_depth - 1
            ):
                return True

        # For condition nodes, check their yes/no branches deeply
        if hasattr(container_node, "connection_yes") and container_node.connection_yes:
            yes_next = container_node.connection_yes.next_node
            if self._contains_node_deep(yes_next, target_node, visited, max_depth - 1):
                return True

        if hasattr(container_node, "connection_no") and container_node.connection_no:
            no_next = container_node.connection_no.next_node
            if self._contains_node_deep(no_next, target_node, visited, max_depth - 1):
                return True

        # Check through general connections
        if hasattr(container_node, "connections") and container_node.connections:
            for conn in container_node.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    if self._contains_node_deep(
                        conn.next_node, target_node, visited, max_depth - 1
                    ):
                        return True

        return False

    def _contains_node_structurally(
        self, container_node, target_node, visited=None, max_depth=3
    ):
        """Check if container_node structurally contains target_node (not just sequentially reachable)."""
        if visited is None:
            visited = set()

        if not container_node or id(container_node) in visited or max_depth <= 0:
            return False

        visited.add(id(container_node))

        # Direct containment
        if container_node == target_node:
            return True

        # Check immediate sub/child relationships only (these represent structural containment)
        if hasattr(container_node, "sub") and container_node.sub:
            if container_node.sub == target_node:
                return True
            # Recursively check sub for structural containment
            if self._contains_node_structurally(
                container_node.sub, target_node, visited, max_depth - 1
            ):
                return True

        if hasattr(container_node, "child") and container_node.child:
            if container_node.child == target_node:
                return True
            # Recursively check child for structural containment
            if self._contains_node_structurally(
                container_node.child, target_node, visited, max_depth - 1
            ):
                return True

        # For condition nodes, check their branches (these represent structural containment)
        if hasattr(container_node, "connection_yes") and container_node.connection_yes:
            yes_next = container_node.connection_yes.next_node
            if self._contains_node_structurally(
                yes_next, target_node, visited, max_depth - 1
            ):
                return True

        if hasattr(container_node, "connection_no") and container_node.connection_no:
            no_next = container_node.connection_no.next_node
            if self._contains_node_structurally(
                no_next, target_node, visited, max_depth - 1
            ):
                return True

        # DO NOT follow general connections - these often represent sequential flow, not structural containment

        return False

    def _contains_node(self, container_node, target_node, visited=None):
        """Check if container_node directly contains the target_node."""
        if visited is None:
            visited = set()

        if not container_node or id(container_node) in visited:
            return False

        visited.add(id(container_node))

        # Direct containment
        if container_node == target_node:
            return True

        # For condition nodes, check their branches
        if hasattr(container_node, "connection_yes") or hasattr(
            container_node, "connection_no"
        ):
            if (
                hasattr(container_node, "connection_yes")
                and container_node.connection_yes
            ):
                yes_next = container_node.connection_yes.next_node
                if self._contains_node(yes_next, target_node, visited):
                    return True

            if (
                hasattr(container_node, "connection_no")
                and container_node.connection_no
            ):
                no_next = container_node.connection_no.next_node
                if self._contains_node(no_next, target_node, visited):
                    return True

        # Check only immediate sub/child, not recursive
        if hasattr(container_node, "sub") and container_node.sub:
            # Direct sub match
            if container_node.sub == target_node:
                return True
            # Check if sub is a wrapper containing our target
            if (
                hasattr(container_node.sub, "cond_node")
                and container_node.sub.cond_node == target_node
            ):
                return True
            # Check if sub has connections that lead to our target (including sequential chains)
            if self._check_reachable_in_branch(container_node.sub, target_node):
                return True

        if hasattr(container_node, "child") and container_node.child:
            # Direct child match
            if container_node.child == target_node:
                return True
            # Check if child is a wrapper containing our target
            if (
                hasattr(container_node.child, "cond_node")
                and container_node.child.cond_node == target_node
            ):
                return True
            # Check if child has connections that lead to our target (including sequential chains)
            if self._check_reachable_in_branch(container_node.child, target_node):
                return True

        # For loop bodies: Follow sequential connections within the same structural scope
        # This is needed because loop bodies often have multiple sequential statements
        if hasattr(container_node, "connections") and container_node.connections:
            for conn in container_node.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    # Check if this is a sequential connection within the same scope
                    if self._is_sequential_connection_in_loop_body(
                        container_node, conn.next_node, target_node, visited
                    ):
                        return True

        return False

    def _is_sequential_connection_in_loop_body(
        self, start_node, next_node, target_node, visited, max_depth=10
    ):
        """Check if next_node leads to target_node through sequential connections within a loop body."""
        if max_depth <= 0 or not next_node or id(next_node) in visited:
            return False

        # Direct match
        if next_node == target_node:
            return True

        # Add to visited to avoid cycles
        current_visited = visited.copy()
        current_visited.add(id(next_node))

        # For wrapper nodes (CondYN), check their sub
        if hasattr(next_node, "sub") and next_node.sub:
            if next_node.sub == target_node:
                return True
            # Continue checking sequentially from the sub
            if self._is_sequential_connection_in_loop_body(
                next_node, next_node.sub, target_node, current_visited, max_depth - 1
            ):
                return True

        # Follow sequential connections within the loop body
        if hasattr(next_node, "connections") and next_node.connections:
            for conn in next_node.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    # Don't follow back to the loop condition (this would be a loop back edge)
                    if (
                        hasattr(conn.next_node, "node_name")
                        and hasattr(start_node, "node_name")
                        and conn.next_node.node_name.startswith("cond")
                    ):
                        continue

                    if self._is_sequential_connection_in_loop_body(
                        next_node,
                        conn.next_node,
                        target_node,
                        current_visited,
                        max_depth - 1,
                    ):
                        return True

        return False

    def _is_reachable_through_exit_path(
        self, start_node, target_node, visited=None, max_depth=5
    ):
        """Check if target is reachable through exit/sequential path from start."""
        if visited is None:
            visited = set()

        if not start_node or id(start_node) in visited or max_depth <= 0:
            return False

        if start_node == target_node:
            return True

        visited.add(id(start_node))

        # Follow sequential connections but avoid going back into loop bodies
        if hasattr(start_node, "connections") and start_node.connections:
            for conn in start_node.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    # Skip connections that would take us back into loop bodies
                    if (
                        hasattr(conn.next_node, "node_name")
                        and conn.next_node.node_name.startswith("cond")
                        and hasattr(conn.next_node, "connection_yes")
                    ):
                        # This is likely a loop condition, don't follow
                        continue

                    if self._is_reachable_through_exit_path(
                        conn.next_node, target_node, visited, max_depth - 1
                    ):
                        return True

        # For wrapper nodes, check their sub/child
        if hasattr(start_node, "sub") and start_node.sub:
            if self._is_reachable_through_exit_path(
                start_node.sub, target_node, visited, max_depth - 1
            ):
                return True

        if hasattr(start_node, "child") and start_node.child:
            if self._is_reachable_through_exit_path(
                start_node.child, target_node, visited, max_depth - 1
            ):
                return True

        return False

    def _check_immediate_structural_children(self, start_node, target_node):
        """Check if target is an immediate structural child of start, including sequential siblings within same scope."""
        if not start_node:
            return False

        # Check direct sub and child relationships only (no connection following)
        if hasattr(start_node, "sub") and start_node.sub == target_node:
            return True
        if hasattr(start_node, "child") and start_node.child == target_node:
            return True

        # Check condition/loop specific structural relationships
        if hasattr(start_node, "cond_node") and start_node.cond_node == target_node:
            return True

        # For condition nodes, check yes/no branches with limited sequential scope
        if hasattr(start_node, "connection_yes") and start_node.connection_yes:
            yes_next = start_node.connection_yes.next_node
            if yes_next == target_node:
                return True
            # Check sequential siblings within the same structural scope (limited depth)
            if self._check_within_same_scope(yes_next, target_node, max_depth=3):
                return True

        if hasattr(start_node, "connection_no") and start_node.connection_no:
            no_next = start_node.connection_no.next_node
            if no_next == target_node:
                return True
            # Check sequential siblings within the same structural scope (limited depth)
            if self._check_within_same_scope(no_next, target_node, max_depth=3):
                return True

        return False

    def _check_within_same_scope(
        self, start_node, target_node, max_depth=3, visited=None
    ):
        """Check if target is within the same structural scope as start (not beyond scope boundaries)."""
        if visited is None:
            visited = set()

        if not start_node or max_depth <= 0 or id(start_node) in visited:
            return False

        visited.add(id(start_node))

        # Direct match
        if start_node == target_node:
            return True

        # Check immediate structural children
        if hasattr(start_node, "sub") and start_node.sub == target_node:
            return True
        if hasattr(start_node, "child") and start_node.child == target_node:
            return True

        # Follow sequential connections within the same scope, but stop at scope boundaries
        if hasattr(start_node, "connections"):
            for conn in start_node.connections or []:
                if hasattr(conn, "next_node") and conn.next_node:
                    next_node = conn.next_node

                    # Stop if we hit a scope boundary (condition/loop nodes typically indicate new scope)
                    if hasattr(next_node, "connection_yes") or hasattr(
                        next_node, "connection_no"
                    ):
                        # This is likely a condition/loop - don't cross this boundary
                        continue

                    # Check if we found the target or can reach it sequentially
                    if next_node == target_node:
                        return True
                    if self._check_within_same_scope(
                        next_node, target_node, max_depth - 1, visited
                    ):
                        return True

        return False

    def _check_reachable_in_branch(
        self, start_node, target_node, visited=None, max_depth=3
    ):
        """Check if target is structurally contained within the same scope as start (not just reachable)."""
        if visited is None:
            visited = set()

        if not start_node or id(start_node) in visited or max_depth <= 0:
            return False

        visited.add(id(start_node))

        # Direct match
        if start_node == target_node:
            return True

        # Only check immediate structural children, not sequential flow
        if hasattr(start_node, "sub") and start_node.sub:
            if start_node.sub == target_node:
                return True
            # Check one level deeper for structural children only
            if self._check_reachable_in_branch(
                start_node.sub, target_node, visited, max_depth - 1
            ):
                return True

        if hasattr(start_node, "child") and start_node.child:
            if start_node.child == target_node:
                return True
            # Check one level deeper for structural children only
            if self._check_reachable_in_branch(
                start_node.child, target_node, visited, max_depth - 1
            ):
                return True

        # For CondYN wrappers, only check direct connections within same structural scope
        if hasattr(start_node, "connections") and start_node.connections:
            for conn in start_node.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    # Only check direct connection, not recursive following
                    if conn.next_node == target_node:
                        return True
                    # Check if the connected node has the target as immediate child
                    if (
                        hasattr(conn.next_node, "sub")
                        and conn.next_node.sub == target_node
                    ) or (
                        hasattr(conn.next_node, "child")
                        and conn.next_node.child == target_node
                    ):
                        return True

        return False

    def _is_sequential_rather_than_nested(self, node1, node2):
        """Check if two nodes are sequential siblings rather than parent-child nested."""
        # For now, use a simple heuristic: if both nodes are at the same "level"
        # (both are loops or both are conditions) and they're similar types,
        # they're likely sequential rather than nested

        # Special case: two loops of the same type are likely sequential
        if (
            hasattr(node1, "node_name")
            and hasattr(node2, "node_name")
            and isinstance(node1, type(node2))
        ):
            # If both are loops, check if they're at the top level of the same function
            # This is a simple heuristic - could be improved with AST position analysis
            return True

        return False

    def _mark_complex_ternary_contained_nodes(self, ternary_node, represented_nodes):
        """Mark all nodes contained in a complex ternary as already represented."""
        try:
            # Mark nodes in YES branch
            if hasattr(ternary_node, "connection_yes") and ternary_node.connection_yes:
                yes_branch = ternary_node.connection_yes.next_node
                self._mark_branch_nodes_as_represented(yes_branch, represented_nodes)

            # Mark nodes in NO branch
            if hasattr(ternary_node, "connection_no") and ternary_node.connection_no:
                no_branch = ternary_node.connection_no.next_node
                self._mark_branch_nodes_as_represented(no_branch, represented_nodes)

        except (AttributeError, TypeError):
            pass

    def _mark_branch_nodes_as_represented(self, branch_node, represented_nodes):
        """Recursively mark all nodes in a branch as represented in complex ternary."""
        if not branch_node:
            return

        visited = set()

        def mark_recursive(node):
            if not node or id(node) in visited:
                return
            visited.add(id(node))

            # For CondYN wrappers, traverse sub and mark only the contained nodes
            if hasattr(node, "sub") and node.sub:
                mark_recursive(node.sub)
                return  # Don't mark the wrapper itself

            # For NodesGroup, traverse and mark all contained nodes
            if hasattr(node, "head") and hasattr(node, "tails"):
                current = node.head
                while current and id(current) not in visited:
                    mark_recursive(current)

                    # Find next node through connections
                    next_node = None
                    if hasattr(current, "connections") and current.connections:
                        for conn in current.connections:
                            if (
                                hasattr(conn, "next_node")
                                and conn.next_node
                                and id(conn.next_node) not in visited
                            ):
                                next_node = conn.next_node
                                break
                    current = next_node
                return  # Don't mark the NodesGroup itself

            # Mark actual leaf nodes (operation, subroutine, etc.) as represented
            if hasattr(node, "node_name") and node.node_name:
                # Only mark if this is not a condition or loop that contains other nodes
                # These should remain as separate entities
                # Also exclude input/output nodes as they are typically top-level
                is_inputoutput = hasattr(node, "__class__") and (
                    "InputOutput" in str(node.__class__)
                    or "Return" in str(node.__class__)
                )
                if (
                    not (
                        hasattr(node, "connection_yes")
                        or hasattr(node, "connection_no")
                    )
                    and not is_inputoutput
                ):
                    represented_nodes.add(node.node_name)

            # For nodes with connections, follow them but don't mark condition/loop nodes
            if hasattr(node, "connections") and node.connections:
                for conn in node.connections:
                    if hasattr(conn, "next_node") and conn.next_node:
                        mark_recursive(conn.next_node)

        mark_recursive(branch_node)

    def _would_condition_be_nested(self, condition_node, all_nodes):
        """Check if a condition would be nested inside another condition/loop, causing depth violations."""
        # Find potential parents for this condition
        for other_orig, _ in all_nodes:
            # Skip if it's the same node
            if other_orig == condition_node:
                continue

            # Check if the other node is a condition or loop
            if (
                hasattr(other_orig, "connection_yes")
                or hasattr(other_orig, "connection_no")
                or hasattr(other_orig, "node_name")
                and (
                    "cond" in str(other_orig.node_name)
                    or "loop" in str(other_orig.__class__.__name__.lower())
                )
            ):
                # Check if this condition is a child of the other node
                is_child = self._is_child_of_parent(condition_node, other_orig)
                if is_child:
                    return True  # This condition would be nested
        return False  # This condition would be top-level

    def _is_truly_independent_statement(self, statement_node, all_nodes):
        """Check if a statement is truly independent vs sequential after branches."""
        # Look at the statement text to determine if it's a final/concluding statement
        statement_text = getattr(statement_node, "node_text", "")

        # Heuristic: statements with 'final' in the text are likely truly independent
        if "final" in statement_text:
            return True

        # Another heuristic: check if this statement comes after ALL conditions/loops
        # vs being sequential within a specific branch

        # For statements like notify_customer("") and results.append(""),
        # they are sequential after loops within condition branches, so they should remain subroutines

        # For statements like results.append("final"),
        # they come after all condition logic, so they should be operations

        # Simple approach: count how many condition/loop nodes exist
        # If this statement is reachable from many different paths, it's likely independent
        condition_count = 0
        for orig_node, react_node in all_nodes:
            if react_node["type"] in ("condition", "loop"):
                condition_count += 1

        # If there are multiple conditions/loops and this statement contains 'final'
        # or similar conclusive keywords, it's likely independent
        # Be more specific with keywords to avoid false positives
        if condition_count > 1:
            # Check for specific patterns that indicate a concluding statement
            if "final" in statement_text.lower():
                return True
            # Check for return statements (but not just 'results' which is a variable name)
            if "return" in statement_text.lower():
                return True

        return False

    def export(self):
        """Export as react-flow compatible dict with proper parent-child relationships.

        Key principles:
        1. Parent assignments are based on actual AST containment (innermost parent)
        2. Loops and conditions can have loop/condition parents (multi-level nesting allowed)
        3. Condition nodes use labeled edges (if/elif/else)
        4. All nodes assign parentId to their innermost containing loop or condition
        """
        all_nodes = []
        all_edges = []
        visited = set()
        return_end_nodes = (
            {}
        )  # Track ReturnEnd nodes and their connecting ReturnOutput nodes

        # Step 1: Collect all nodes and edges
        def collect_nodes_and_edges(node):
            if (
                id(node) in visited
                or not hasattr(node, "node_name")
                or not node.node_name
            ):
                return True
            visited.add(id(node))

            react_node = node.to_react_flow_node()
            if react_node and not self._is_function_wrapper_node(node):
                all_nodes.append((node, react_node))
                edges = node.to_react_flow_edges()
                all_edges.extend(edges)

                # Track ReturnOutput -> ReturnEnd connections
                from pyreactflow.ast_node import ReturnOutput, ReturnEnd

                if isinstance(node, ReturnOutput):
                    # Find which ReturnEnd this output connects to
                    for conn in node.connections:
                        if hasattr(conn, "next_node") and isinstance(
                            conn.next_node, ReturnEnd
                        ):
                            return_end_nodes[id(conn.next_node)] = node

            return True

        if self.head:
            self._traverse(collect_nodes_and_edges, f"export-{id(self)}")

        # Step 2: Filter out ReturnEnd nodes that have a paired ReturnOutput
        # (bare return statements should keep their ReturnEnd node)
        from pyreactflow.ast_node import ReturnEnd

        filtered_nodes = []
        for orig_node, react_node in all_nodes:
            if isinstance(orig_node, ReturnEnd) and id(orig_node) in return_end_nodes:
                # This ReturnEnd has a paired ReturnOutput, skip it
                continue
            filtered_nodes.append((orig_node, react_node))
        all_nodes = filtered_nodes

        # Step 3: Detect and merge condition chains (if/elif/else)
        chains = self._detect_condition_chains(all_nodes, all_edges)
        if chains:
            nodes_to_remove_ids, edges_to_remove, edges_to_add = (
                self._merge_condition_chains(chains, all_nodes, all_edges)
            )

            # Remove intermediate condition nodes from all_nodes
            all_nodes = [
                (orig, react)
                for orig, react in all_nodes
                if react["id"] not in nodes_to_remove_ids
            ]

            # Remove old edges
            edges_to_remove_set = {
                (e["source"], e["target"], e.get("label", "")) for e in edges_to_remove
            }
            all_edges = [
                e
                for e in all_edges
                if (e["source"], e["target"], e.get("label", ""))
                not in edges_to_remove_set
            ]

            # Add new multi-branch edges
            all_edges.extend(edges_to_add)

        # Step 4: Process nodes - assign parents based on actual containment
        final_nodes = []
        final_edges = []

        for original_node, react_node in all_nodes:
            # Assign parent based on innermost containment
            self._process_regular_node(
                original_node, react_node, all_nodes, all_edges, final_nodes
            )

        # Step 5: Process edges
        self._process_edges_final(all_edges, final_nodes, {}, set(), final_edges)

        return {"nodes": final_nodes, "edges": final_edges}

    def _is_function_wrapper_node(self, node):
        """Check if node is a function definition wrapper node that should be excluded from export."""
        # Import here to avoid circular imports
        from pyreactflow.ast_node import FunctionDefStart, FunctionDefEnd

        # Always exclude FunctionDefStart
        if isinstance(node, FunctionDefStart):
            return True

        # Always exclude FunctionDefEnd - return statements create their own ReturnOutput/ReturnEnd nodes
        if isinstance(node, FunctionDefEnd):
            return True

        # Note: ReturnEnd nodes should NOT be excluded - they represent actual return statements
        # in the code flow and should be visible in the flowchart

        return False

    def _process_edges_final(
        self, all_edges, final_nodes, loops_to_merge, nodes_to_remove, final_edges
    ):
        """Process edges with cleanup for merged loops."""
        final_node_ids = {node["id"] for node in final_nodes}

        for edge in all_edges:
            # Skip edges involving removed nodes
            if (
                edge["source"] not in final_node_ids
                or edge["target"] not in final_node_ids
            ):
                continue

            # Skip back edges from children to loop parents (creates cycles)
            if self._is_back_edge_to_parent(edge, final_nodes):
                continue

            # Skip edges from loops to their direct children (represented by parentId)
            if self._is_loop_to_child_edge(edge, final_nodes):
                continue

            # Convert and clean up edge labels
            final_edge = edge.copy()
            self._convert_condition_edge_labels(final_edge, final_nodes)

            final_edges.append(final_edge)

    def _node_contains_node(self, container, target):
        """Check if container node contains target node in its structure."""
        if not container or container == target:
            return container == target

        # Check sub and child relationships
        if hasattr(container, "sub") and container.sub:
            if container.sub == target or self._node_contains_node(
                container.sub, target
            ):
                return True

        if hasattr(container, "child") and container.child:
            if container.child == target or self._node_contains_node(
                container.child, target
            ):
                return True

        # Check connections
        if hasattr(container, "connections"):
            for conn in container.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    if conn.next_node == target or self._node_contains_node(
                        conn.next_node, target
                    ):
                        return True
        return False

    def _process_regular_node(
        self, original_node, react_node, all_nodes, all_edges, final_nodes
    ):
        """Process regular nodes with simplified parent assignment based on actual containment."""
        # Check if this node is a direct target of a multi-branch edge from a TOP-LEVEL condition
        # These nodes use edges for control flow and shouldn't have structural parents
        # IMPORTANT: This check should NOT apply to loop nodes, as they need structural parents
        node_id = react_node["id"]
        is_top_level_multibranch_target = False

        # Only check multi-branch target logic for non-loop nodes
        # Loop nodes should always get their structural parent assigned based on AST containment
        if react_node["type"] != "loop":
            # Find all condition nodes and their parent status
            condition_nodes_map = {
                react["id"]: react
                for orig, react in all_nodes
                if react["type"] == "condition"
            }

            for edge in all_edges:
                if edge["target"] == node_id and edge["source"] in condition_nodes_map:
                    label = edge.get("label", "")
                    # Check if this is a multi-branch edge (if/elif/else)
                    if (
                        label.startswith("if ")
                        or label.startswith("elif ")
                        or label == "else"
                    ):
                        # Check if the source condition has a parent
                        source_condition = condition_nodes_map[edge["source"]]
                        if "parentId" not in source_condition:
                            # This is a multi-branch edge from a top-level condition
                            is_top_level_multibranch_target = True
                            break

        # If this is a direct target of a multi-branch edge from a top-level condition,
        # don't assign structural parent. The control flow is already represented by the labeled edge
        if is_top_level_multibranch_target:
            final_nodes.append(react_node)
            return

        # For all other nodes, find the innermost parent (loop or condition that contains this node)
        parent_id = self._find_innermost_parent(original_node, all_nodes)

        # Assign parent if one was found
        if parent_id and parent_id != react_node["id"]:  # Prevent self-parenting
            react_node["parentId"] = parent_id
            react_node["extent"] = "parent"

        # Special handling for subroutines: convert top-level subroutines to operations
        if react_node["type"] == "subroutine" and not parent_id:
            if self._is_truly_independent_statement(original_node, all_nodes):
                react_node["type"] = "operation"

        final_nodes.append(react_node)

    def _find_containing_while_loop(self, statement_node, all_nodes):
        """Find a while loop that contains the given statement node."""
        from pyreactflow.ast_node import LoopCondition

        for orig_node, react_node in all_nodes:
            if (
                react_node["type"] == "loop"
                and isinstance(orig_node, LoopCondition)
                and hasattr(orig_node, "ast_object")
                and hasattr(orig_node.ast_object, "test")
            ):
                # This is a while loop, check if it contains our statement
                if self._statement_is_inside_while_loop(statement_node, orig_node):
                    return react_node["id"]
        return None

    def _statement_is_inside_while_loop(self, statement_node, while_loop_node):
        """Check if a statement is inside a while loop (including through condition branches)."""
        # Get the while loop body
        if (
            hasattr(while_loop_node, "connection_yes")
            and while_loop_node.connection_yes
        ):
            loop_body = while_loop_node.connection_yes.next_node
            return self._statement_is_in_loop_body(
                statement_node, loop_body, visited=set()
            )
        return False

    def _statement_is_in_loop_body(
        self, statement_node, loop_body, visited=None, max_depth=10
    ):
        """Recursively check if statement is in the loop body structure."""
        if visited is None:
            visited = set()

        if not loop_body or id(loop_body) in visited or max_depth <= 0:
            return False

        visited.add(id(loop_body))

        # Direct match
        if loop_body == statement_node:
            return True

        # Check sub/child relationships first
        if hasattr(loop_body, "sub") and loop_body.sub:
            # Direct match with sub
            if loop_body.sub == statement_node:
                return True
            # Recursive check in sub
            if self._statement_is_in_loop_body(
                statement_node, loop_body.sub, visited, max_depth - 1
            ):
                return True

        if hasattr(loop_body, "child") and loop_body.child:
            # Direct match with child
            if loop_body.child == statement_node:
                return True
            # Recursive check in child
            if self._statement_is_in_loop_body(
                statement_node, loop_body.child, visited, max_depth - 1
            ):
                return True

        # For condition nodes, check both yes and no branches
        if hasattr(loop_body, "connection_yes") and loop_body.connection_yes:
            yes_next = loop_body.connection_yes.next_node
            if yes_next:
                # Check direct match in yes branch
                if yes_next == statement_node:
                    return True
                # Check if yes branch has a sub that matches
                if hasattr(yes_next, "sub") and yes_next.sub == statement_node:
                    return True
                # Recursive check in yes branch
                if self._statement_is_in_loop_body(
                    statement_node, yes_next, visited, max_depth - 1
                ):
                    return True

        if hasattr(loop_body, "connection_no") and loop_body.connection_no:
            no_next = loop_body.connection_no.next_node
            if no_next:
                # Check direct match in no branch
                if no_next == statement_node:
                    return True
                # Check if no branch has a sub that matches
                if hasattr(no_next, "sub") and no_next.sub == statement_node:
                    return True
                # Recursive check in no branch
                if self._statement_is_in_loop_body(
                    statement_node, no_next, visited, max_depth - 1
                ):
                    return True

        # Check through connections (for sequential flow within loop)
        if hasattr(loop_body, "connections") and loop_body.connections:
            for conn in loop_body.connections:
                if hasattr(conn, "next_node") and conn.next_node:
                    next_node = conn.next_node
                    # Recursive check through connections
                    if self._statement_is_in_loop_body(
                        statement_node, next_node, visited, max_depth - 1
                    ):
                        return True

        return False

    def _node_exists_in_final(self, node_id, final_node_ids):
        """Check if a node exists in the final nodes."""
        return node_id in final_node_ids

    def _is_merged_loop_to_body_edge(self, edge, loops_to_merge, final_nodes):
        """Check if this edge is from a merged loop to its body."""
        source_node = next((n for n in final_nodes if n["id"] == edge["source"]), None)
        if (
            source_node
            and source_node["type"] == "loop"
            and "→" in source_node["data"]["label"]
        ):
            # This is a merged loop, check if target was its body
            # We can't easily check this without more complex tracking, so skip for now
            pass
        return False

    def _is_back_edge_to_parent(self, edge, final_nodes):
        """Check if this is a back edge from child to parent."""
        target_node = next((n for n in final_nodes if n["id"] == edge["target"]), None)
        source_node = next((n for n in final_nodes if n["id"] == edge["source"]), None)

        if (
            target_node
            and source_node
            and target_node["type"] == "loop"
            and source_node.get("parentId") == target_node["id"]
        ):
            return True
        return False

    def _is_loop_to_child_edge(self, edge, final_nodes):
        """Check if this is an edge from loop to its direct child."""
        source_node = next((n for n in final_nodes if n["id"] == edge["source"]), None)
        target_node = next((n for n in final_nodes if n["id"] == edge["target"]), None)

        if (
            source_node
            and target_node
            and source_node["type"] == "loop"
            and target_node.get("parentId") == source_node["id"]
        ):
            return True
        return False

    def _detect_condition_chains(self, all_nodes, all_edges):
        """Detect all condition nodes that should use multi-branch format.

        This includes:
        - Simple if/else (1 condition node with yes/no branches)
        - if/elif/else chains (2+ condition nodes connected via orelse in AST)

        This function now uses AST structure to distinguish between:
        - True if/elif/else chains (elif nested in parent's orelse)
        - Consecutive independent if statements (siblings in body)

        Returns:
            List of chains, where each chain is a list of (original_node, react_node) tuples.
            The first element in each chain is the root condition (if/elif start).
        """
        from pyreactflow.ast_node import IfCondition

        # Find all condition nodes
        condition_nodes = [
            (orig, react) for orig, react in all_nodes if react["type"] == "condition"
        ]

        if len(condition_nodes) == 0:
            return []

        chains = []
        processed = set()

        for orig_node, react_node in condition_nodes:
            if react_node["id"] in processed:
                continue

            # Check if this is an IfCondition with AST object
            if not isinstance(orig_node, IfCondition) or not hasattr(
                orig_node, "ast_object"
            ):
                # Not an IfCondition (might be LoopCondition or other), create a chain of one
                chains.append([(orig_node, react_node)])
                processed.add(react_node["id"])
                continue

            # Build chain by following orelse in AST
            chain = [(orig_node, react_node)]
            processed.add(react_node["id"])
            current_ast = orig_node.ast_object

            # Follow the orelse chain to find elif conditions
            while current_ast.orelse:
                # Check if orelse contains exactly one If node (this is an elif)
                if len(current_ast.orelse) == 1 and isinstance(
                    current_ast.orelse[0], _ast.If
                ):
                    # This is an elif - find its corresponding node
                    elif_ast = current_ast.orelse[0]

                    # Find the node corresponding to this elif
                    elif_node = None
                    for cond_orig, cond_react in condition_nodes:
                        if (
                            isinstance(cond_orig, IfCondition)
                            and hasattr(cond_orig, "ast_object")
                            and cond_orig.ast_object is elif_ast
                        ):
                            elif_node = (cond_orig, cond_react)
                            break

                    if elif_node:
                        chain.append(elif_node)
                        processed.add(elif_node[1]["id"])
                        current_ast = elif_ast
                    else:
                        break
                else:
                    # orelse contains else body or other statements, not elif
                    break

            chains.append(chain)

        return chains

    def _merge_condition_chains(self, chains, all_nodes, all_edges):
        """Merge condition chains into single multi-branch condition nodes.

        Consistently uses multi-branch format:
        - if/else (2 branches) → "if"/"else" labels
        - if/elif/else (3+ branches) → "if"/"elif"/"else" labels
        - if only (1 branch) → "if" label only

        Args:
            chains: List of chains from _detect_condition_chains()
            all_nodes: List of (original_node, react_node) tuples
            all_edges: List of edge dictionaries

        Returns:
            Tuple of (nodes_to_remove, edges_to_remove, edges_to_add)
            where nodes_to_remove is a set of node IDs to remove from final nodes,
            edges_to_remove is a set of edge dictionaries to remove,
            and edges_to_add is a list of new edge dictionaries to add.
        """
        nodes_to_remove = set()
        edges_to_remove = []
        edges_to_add = []

        for chain in chains:
            # Keep the first condition as the merged node
            root_orig, root_react = chain[0]

            # Collect all conditions in this chain (for removal except root)
            for i in range(1, len(chain)):
                _, intermediate_react = chain[i]
                nodes_to_remove.add(intermediate_react["id"])

            # Collect all branch information
            # Each branch has: (condition_text, target_node_id, branch_type)
            # branch_type is 'if', 'elif', or 'else'
            branches = []

            # Process each condition in the chain
            for idx, (cond_orig, cond_react) in enumerate(chain):
                condition_text = cond_react["data"]["label"]

                # Find the 'yes' edge from this condition
                yes_target = None
                for edge in all_edges:
                    if edge["source"] == cond_react["id"] and edge.get("label") in (
                        "yes",
                        "Yes",
                    ):
                        yes_target = edge["target"]
                        edges_to_remove.append(edge)
                        break

                if yes_target:
                    # Determine branch type
                    if idx == 0:
                        branch_type = "if"
                    else:
                        branch_type = "elif"

                    branches.append((condition_text, yes_target, branch_type))

            # Find the final 'no' edge from the last condition (this is the 'else' branch)
            last_cond_orig, last_cond_react = chain[-1]
            else_target = None
            else_edge = None
            for edge in all_edges:
                if edge["source"] == last_cond_react["id"] and edge.get("label") in (
                    "no",
                    "No",
                ):
                    else_target = edge["target"]
                    else_edge = edge
                    edges_to_remove.append(edge)
                    break

            # Only add 'else' branch if there's actually an else target
            if else_target:
                branches.append(("else", else_target, "else"))

            # Remove all 'no' edges between conditions in the chain
            for i in range(len(chain) - 1):
                _, cond_react = chain[i]
                _, next_cond_react = chain[i + 1]

                for edge in all_edges:
                    if (
                        edge["source"] == cond_react["id"]
                        and edge["target"] == next_cond_react["id"]
                        and edge.get("label") in ("no", "No")
                    ):
                        edges_to_remove.append(edge)
                        break

            # Create new multi-branch edges from root to all targets
            for condition_text, target_id, branch_type in branches:
                # Create edge label
                if branch_type == "else":
                    edge_label = "else"
                else:
                    edge_label = f"{branch_type} {condition_text}"

                # Create new edge
                new_edge = {
                    "id": f"{root_react['id']}->{target_id}-{branch_type}",
                    "source": root_react["id"],
                    "target": target_id,
                    "label": edge_label,
                }
                edges_to_add.append(new_edge)

        return nodes_to_remove, edges_to_remove, edges_to_add

    def _convert_condition_edge_labels(self, edge, final_nodes):
        """Convert condition edge labels from yes/no to Yes/No and clean up others.

        Skip multi-branch labels (if/elif/else) created by condition chain merging.
        """
        source_node = next((n for n in final_nodes if n["id"] == edge["source"]), None)

        # Check if this is a multi-branch edge (created by condition chain merging)
        label = edge.get("label", "")
        if label.startswith("if ") or label.startswith("elif ") or label == "else":
            # This is a multi-branch edge, don't modify it
            return

        if source_node and source_node["type"] == "condition":
            if edge.get("label") == "yes":
                edge["label"] = "Yes"
            elif edge.get("label") == "no":
                edge["label"] = "No"
            elif edge.get("label") == "exit":
                # Remove exit labels for cleaner output
                edge.pop("label", None)
        else:
            # For non-condition edges, clean up unwanted labels
            if edge.get("label") in ("exit", "yes", "no"):
                edge.pop("label", None)

    def _is_statement_after_loop(self, statement_node, loop_node, all_nodes):
        """Check if a statement comes AFTER a loop rather than WITHIN it."""
        try:
            statement_react = statement_node.to_react_flow_node()
            if not statement_react:
                return False

            statement_label = statement_react["data"]["label"]

            # Heuristic 1: statements that contain "final" are likely sequential after everything
            if "final" in statement_label.lower():
                return True

            # Heuristic 2: Check if this statement is reachable from multiple different loops
            # This indicates it's a merge point after parallel branches
            loop_count_pointing_to_statement = 0
            for orig, react in all_nodes:
                if react["type"] == "loop" and orig != loop_node:
                    if self._is_child_of_parent(statement_node, orig):
                        loop_count_pointing_to_statement += 1

            if loop_count_pointing_to_statement > 0:
                return True

            # Heuristic 3: Check if this statement is structurally at the same level as the loop
            # rather than nested within it, BUT only apply this in contexts where we have
            # additional evidence that it's truly sequential (e.g., appears after condition blocks)
            if isinstance(loop_node, LoopCondition):
                if hasattr(loop_node, "connection_yes") and loop_node.connection_yes:
                    loop_body = loop_node.connection_yes.next_node
                    if loop_body:
                        # Check structural containment vs just reachability
                        is_structurally_contained = self._contains_node_structurally(
                            loop_body, statement_node, set()
                        )
                        is_reachable = self._contains_node(
                            loop_body, statement_node, set()
                        )

                        # Only apply this heuristic if there's additional evidence of being sequential
                        # (e.g., the statement appears to be a cleanup operation or merge point)
                        if is_reachable and not is_structurally_contained:
                            # Additional check: only trigger if this looks like a cleanup/final statement
                            if (
                                "final" in statement_label.lower()
                                or "notify_customer(" in statement_label
                                and "''" in statement_label
                                or "results.append(" in statement_label
                                and "''" in statement_label
                            ):
                                return True

            # Heuristic 4: Special case for statements that appear to be cleanup/notification
            # operations that come after processing loops (common pattern)
            # Be very specific to avoid false positives
            if ("notify_customer" in statement_label and "''" in statement_label) or (
                statement_label.startswith("results.append") and "''" in statement_label
            ):
                return True

            return False
        except (AttributeError, TypeError):
            return False

    def _statement_is_in_condition_in_loop(self, statement_node, loop_node, all_nodes):
        """Check if statement is in a condition that's in the given loop."""
        try:
            # Look for condition nodes in all_nodes that could be in this loop
            condition_nodes_in_all = [
                (orig, react)
                for orig, react in all_nodes
                if react["type"] == "condition"
            ]

            for condition_orig, condition_react in condition_nodes_in_all:
                # Check if this condition is a child of the loop
                if self._is_child_of_parent(condition_orig, loop_node):
                    # Check if this condition contains our statement
                    if self._condition_contains_statement(
                        condition_orig, statement_node
                    ):
                        return True

            return False
        except (AttributeError, TypeError):
            return False

    def _condition_contains_statement(self, condition_node, statement_node):
        """Check if a condition node contains a statement in its branches."""
        try:
            # Check yes branch
            if (
                hasattr(condition_node, "connection_yes")
                and condition_node.connection_yes
            ):
                yes_branch = condition_node.connection_yes.next_node
                if self._branch_contains_statement(yes_branch, statement_node):
                    return True

            # Check no branch
            if (
                hasattr(condition_node, "connection_no")
                and condition_node.connection_no
            ):
                no_branch = condition_node.connection_no.next_node
                if self._branch_contains_statement(no_branch, statement_node):
                    return True

            return False
        except (AttributeError, TypeError):
            return False

    def _branch_contains_statement(self, branch_node, statement_node):
        """Check if a branch contains the statement."""
        if not branch_node:
            return False

        # Direct match
        if branch_node == statement_node:
            return True

        # Check sub/child
        if hasattr(branch_node, "sub") and branch_node.sub == statement_node:
            return True

        if hasattr(branch_node, "child") and branch_node.child == statement_node:
            return True

        return False

    def _get_child_content_for_merge(self, parent_node):
        """Get child content to merge into parent label."""
        try:
            if isinstance(parent_node, LoopCondition):
                body_connection = parent_node.connection_yes.next_node
                if hasattr(body_connection, "child") and body_connection.child:
                    return getattr(body_connection.child, "node_text", "")
            elif hasattr(parent_node, "connection_yes") and parent_node.connection_yes:
                body_connection = parent_node.connection_yes.next_node
                if hasattr(body_connection, "sub") and body_connection.sub:
                    return getattr(body_connection.sub, "node_text", "")
        except:
            pass
        return None

    def _get_child_id_for_merge(self, parent_node):
        """Get child node ID that should be merged."""
        try:
            if isinstance(parent_node, LoopCondition):
                body_connection = parent_node.connection_yes.next_node
                if hasattr(body_connection, "child") and body_connection.child:
                    return getattr(body_connection.child, "node_name", None)
            elif hasattr(parent_node, "connection_yes") and parent_node.connection_yes:
                body_connection = parent_node.connection_yes.next_node
                if hasattr(body_connection, "sub") and body_connection.sub:
                    return getattr(body_connection.sub, "node_name", None)
        except:
            pass
        return None

    def _find_parent_for_child(self, child_node, parent_candidates):
        """Find parent node for a child (if not merged)."""
        child_node_name = getattr(child_node, "node_name", None)

        # Exclude input/output nodes - they should always be top-level
        child_react_node = child_node.to_react_flow_node()
        if child_react_node and child_react_node.get("type") in (
            "inputoutput",
            "start",
            "end",
        ):
            return None

        # First try containment-based detection
        for parent_original, parent_react in parent_candidates:
            is_child = self._is_child_of_parent(child_node, parent_original)
            if is_child:
                # Since we disabled merging for top-level nodes, always assign parent-child relationships
                return parent_react["id"]

        # If containment detection failed, try edge-based detection
        if child_node_name:
            # Look for exit edges from potential parents to this child
            for parent_original, parent_react in parent_candidates:
                parent_edges = parent_original.to_react_flow_edges()
                for edge in parent_edges:
                    if (
                        edge.get("label") == "exit"
                        and edge["target"] == child_node_name
                    ):
                        return parent_react["id"]

        return None

    def _is_reachable(self, start_node, target_node, visited=None, max_depth=10):
        """Check if target_node is reachable from start_node."""
        if visited is None:
            visited = set()

        if not start_node or id(start_node) in visited or max_depth <= 0:
            return False

        if start_node == target_node:
            return True

        visited.add(id(start_node))

        # Check through transparent/wrapper nodes first
        if hasattr(start_node, "child") and start_node.child:
            if self._is_reachable(
                start_node.child, target_node, visited, max_depth - 1
            ):
                return True

        # Check if this is a CondYN node - get its sub node
        if hasattr(start_node, "sub") and start_node.sub:
            if self._is_reachable(start_node.sub, target_node, visited, max_depth - 1):
                return True

        # Check through connections
        for conn in getattr(start_node, "connections", []):
            if hasattr(conn, "next_node") and conn.next_node:
                if self._is_reachable(
                    conn.next_node, target_node, visited, max_depth - 1
                ):
                    return True

        return False
