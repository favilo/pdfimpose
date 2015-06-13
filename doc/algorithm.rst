Algorithm
=========

*Note: Explaining an algorithm can be very technical. It is even more as English is not my main language. Sorry. Feel free to improve it!*

The main algorithm in this program is the algorithm building the
:class:`pdfimpose.ImpositionMatrix`, which is a matrix of oriented pages. It
represents the way pages of the source document are imposed into the
destination page, both in position and orientation.

First page is page 0.

Recto
-----

We start with an empty matrix, and we put the first page in the bottom left
orner (this can change depending on binding; see next section):

     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     | 0  |    |    |    |
     +----+----+----+----+

A key concept is the concept of *virtual page*. A virtual page is a page we get
after several folds. For instance, the matrix above has one virtual page (got
after zero folds), numbered 0.

Each time we fold the page, we fold each virtual page along the same direction.
For each of the virtual page:

* We split it in two virtual pages (according to the fold direction). One of them contains the original page number, the other is empty.
* We put a new number on the location which is symetrical to the location of
  the original page number. The page number is such that the sum of old and new
  page number is equal to the number of virtual pages, minus one.
* Orientation of the new page is :

  * if fold is horizontal: keep page orientation;
  * if fold is vertical: reverse page orientation.

Example
-------

*In this example, we fold horizontally, vertically, horizontally, vertically.*

Upside-down pages are marked with an asterisk*.

* Initialisation

     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     | 0  |    |    |    |
     +----+----+----+----+

* We fold horizontally this unique virtual page. There are two virtual pages,
  so the new page number will be 1 (as ``0+1=2-1``). There is no rotation since
  the fold is horizontal.

     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     | 0  |    |    | 1  |
     +----+----+----+----+

* We fold vertically the two virtual pages (one left, one right). In each
  virtual page, the sum of the old and new page number must be 3 (four virtual
  pages, minus one). They are rotated, since fold is vertical.

     +----+----+----+----+
     | 3* |    |    | 2* |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     | 0  |    |    | 1  |
     +----+----+----+----+

* And so on: four virtual pages becoming eight virtual pages with an
  horizontal fold.

     +----+----+----+----+
     | 3* | 4* | 5* | 2* |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     |    |    |    |    |
     +----+----+----+----+
     | 0  | 7  | 6  | 1  |
     +----+----+----+----+

* One other vertical fold, making 16 virtual pages from 8 virtual pages.

     +----+----+----+----+
     | 3* | 4* | 5* | 2* |
     +----+----+----+----+
     | 12 | 11 | 10 | 13 |
     +----+----+----+----+
     | 15*| 8* | 9* | 14*|
     +----+----+----+----+
     | 0  | 7  | 6  | 1  |
     +----+----+----+----+

Recto-verso
-----------

The algorithm described so far only displays one side (recto) of a page. To
print the other side, we simply add an horizontal fold at the beginning of
every folds.

Imagine you want to print a page of A4 paper, but your printer does not print
two-sided. What you can do is print both sides of your A4 page side-to-side on
an A3 page (twice as big), print this A3 page, and fold your page. You get a
two-sided A4 paper.

This is why we simply add an horizontal fold at the beginning of every folds.
Then, imposition matrix for each pages can be extracted using methods
:meth:`pdfimpose.ImpositionMatrix.recto` and
:meth:`pdfimpose.ImpositionMatrix.verso`.

Binding
-------

Top, bottom, left, right binding affects:

* the position and orientation of the first page;
* whether pages should be rotated on the first fold (the recto-verso fold) or
  not.
