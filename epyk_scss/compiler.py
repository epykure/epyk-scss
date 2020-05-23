
import os
import importlib
import inspect
import operator


from epyk.core.css import Defaults as default_css
from epyk.core.html import Defaults as default_html
from epyk.core.css import themes


SCSS_VAR = {
  '$line_height': '%spx' % default_html.LINE_HEIGHT,
  '$font_size': '%spx' % default_html.LINE_HEIGHT,
}

SCSS_MAP = {
  "line-height: %spx" % default_html.LINE_HEIGHT: "line-height: $line_height",
  'font-size: %spx' % default_css.Font.size: "font-size: $font_size",
}


class Scss(object):

  categories = ('_charts', '_colors', '_greys', '_warning', '_danger', '_success')

  def __init__(self, filename, path=None):
    self.filename, self.outpaht = filename, path
    self.__colors_map, self.themes = {}, {}
    self._css_data = ""
    file_path = os.path.join(path, filename) if path is not None else filename
    with open(file_path) as f:
      self._css_data = f.read()

  def get_themes(self):
    """
    Description:
    ------------
    Loads all the themes to deduce the one used to generate this report.
    This will then add all the default other colors to the global theme scss file.
    """
    for theme_file in os.listdir(os.path.dirname(themes.__file__)):
      if theme_file.endswith(".py"):
        mod = importlib.import_module("epyk.core.css.themes.%s" % theme_file[:-3])
        for theme in inspect.getmembers(mod, inspect.isclass):
          if theme[0] != 'Theme':
            self.themes[theme[0]] = theme[1]
            for theme_attr in self.categories:
              for c in getattr(theme[1], theme_attr):
                if c not in self.__colors_map:
                  self.__colors_map[c] = set()
                self.__colors_map[c].add(theme[0])

  def deduce_theme(self):
    """
    Description:
    ------------

    """
    if not self.__colors_map:
      self.get_themes()
    count_themes = {}
    for color, themes in self.__colors_map.items():
      occurences = self._css_data.count(color)
      if occurences:
        for t in themes:
          count_themes[t] = count_themes.get(t, 0) + occurences
    return sorted(count_themes.items(), key=operator.itemgetter(1), reverse=True)[0][0]

  def complie(self, path=None):
    """
    Description:
    ------------

    Attributes:
    ----------
    :param path: String.
    """
    theme = self.deduce_theme()
    path = path or self.outpaht
    file_path = os.path.join(path, "scss_theme_%s" % self.filename) if path is not None else "scss_theme_%s" % self.filename

    # Create a file with the default and theme values
    # replace by variables in the scss files
    scss_vars = {}
    with open(file_path, "w") as f:
      for cat in self.categories:
        colors = getattr(self.themes[theme], cat)
        f.write("$%s: %s;\n" % (cat[1:], ", ".join(colors)))
        for i, c in enumerate(colors):
          scss_vars[c] = "nth($%s, %s)" % (cat[1:], i+1) # scss list starts at 1

      f.write("\n")
      for k, v in SCSS_VAR.items():
        f.write("%s: %s ; \n" % (k, v))

    file_path = os.path.join(path, "scss_%s" % self.filename) if path is not None else "scss_%s" % self.filename
    with open(file_path, "w") as f:
      for k, v in scss_vars.items():
        self._css_data = self._css_data.replace(k, v)
      for k, v in SCSS_MAP.items():
        self._css_data = self._css_data.replace(k, v)
      f.write(self._css_data)
