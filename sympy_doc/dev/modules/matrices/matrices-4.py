A = Matrix([[1, 2], [2, -1]])
A.is_indefinite
# True

p = plot3d((x.T*A*x)[0, 0], (a, -1, 1), (b, -1, 1))
