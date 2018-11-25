import re
import logging
import string
import math
import nltk

logger = logging.getLogger(__file__)

# Regular expression to separate the paragraphs of the input
# text into separate strings.
paragraph_regex = re.compile('\n\n+', re.UNICODE)

class Transpiler:

    def transpile(self, text):
        paragraphs = self.tokenize_paragraphs(text)
        logger.debug('paragraphs: {}'.format(paragraphs))

        self.produce_class_code({
            'name': 'Dog',
            'attributes': {
                'mood': 'HAPPY',
                'energy': 100,
                'coordinatePosition': (0, 0)
            }
        })

    def split_paragraphs(self, text):
        '''
        Returns a list of strings. Each strings is a paragraph in the
        given text.
    
        Arguments:
        text -- string assumed to contain one or more paragraphs, where a
          paragraph is defined as consecutive lines, i.e. two consecutive
          line breaks demarcate a paragraph.
        
        Usage:
        >>> two_paragraphs_together = """this is the
        ... first paragraph
        ...
        ... and this is the
        ... second
        ... """
        >>> transpiler = Transpiler()
        >>> separated_paragraphs = transpiler.split_paragraphs(two_paragraphs_together)
        >>> print(separated_paragraphs[0])
        this is the
        first paragraph
        >>> print(separated_paragraphs[1])
        and this is the
        second
        '''
        return list(map(lambda s: s.strip('\n'), paragraph_regex.split(text)))
    
    def parse_class_paragraph(self, paragraph):
        '''Returns a dictionary that contains an internal representation of
        a python class given as a natural language string *paragraph*.
        
        Arguments:
        paragraph -- str, Natural language string describing a python class.
        
        Usage:
        >>> paragraph = """
        ... A dog is a Class. He has mood = "HAPPY", energy = 100,
        ... x = 0, y = 0 . He can Bark, Run, MoveLeft, MoveRight,
        ... MoveForward, Lay and Check. To Run he used MoveForward(2), his energy
        ... decreases in 1, his mood is "PLAY" and return 0, end. To MoveForward he
        ... needs numbersSteps, his y increases in
        ... numbersSteps, his mood is "MOVING", his energy decreases by 1, end. To MoveLeft
        ... he needs numbersSteps, his x decreases in
        ... numbersSteps, his mood is "MOVING", his energy decreases by 1, end. To
        ... MoveRight he needs numbersSteps, his x increases
        ... in numbersSteps, his mood is "MOVING", his energy decreases by 1, end. To Bark
        ... he print "barf barf", his energy decreases by 1, his mood is
        ... "BARKING", end. To Lay he used print "relax", he used print "move the
        ... Booty", his energy increases in 3, end. To Check he print "mood: " +
        ... self.mood, he print "energy: " + str(self.energy), he print "Position" +
        ... str(self.coordinatePosition), end.
        ... """
        >>> transpiler = Transpiler()
        >>> class_metadata = transpiler.parse_class_paragraph(paragraph)
        >>> class_metadata['class_name']
        'dog'
        >>> class_metadata['property_names_and_defaults']
        [('mood', '"happy"'), ('energy', '100'), ('x', '0'), ('y', '0')]
        >>> class_metadata['method_names']
        ['bark', 'run', 'moveleft', 'moveright', 'moveforward', 'lay', 'check']
        '''
        # 1. Lowercase paragraph
        lowercase_paragraph = paragraph.lower()
        # 2. Tokenize words
        word_tokens = self.tokenize_words(lowercase_paragraph)
        # 3. POS-tagging
        tagged_word_tokens = self.part_of_speech_tag(word_tokens)
    
        class_name = None
        class_keyword_index = word_tokens.index('class')
        first_noun_before_class_keyword = next(filter(
            lambda pair: pair[1] == 'NN',
            tagged_word_tokens[class_keyword_index-1:0:-1]))[0]
        class_name = first_noun_before_class_keyword
        
    
        property_names_and_defaults = []
        index_of_first_word_second_sentence = (
            class_keyword_index +
            1 + # Because of the dot that finalizes the class declaration
            1 # the word after the dot
        )
        
        i = 0
        j = index_of_first_word_second_sentence
        while True:
            next_word = word_tokens[j + i]
            if next_word == '.':
                break
        
            if next_word == '=':
                # The property name is the word before the = symbol
                property_name = word_tokens[j + i - 1]
        
                # The property default value is the concatenations of all
                # the words/tokens after the = symbol and before the next
                # immediate comma or period.
                property_default_value = ''
        
                i += 1
                next_word = word_tokens[j + i]
        
                while next_word not in ('.', ','):
                    property_default_value += next_word
                    i += 1
                    next_word = word_tokens[j + i]
        
                # Something weird happens where string value, i.e. with double quotes
                # are parsed as beginning with 2 of this symbol: '`'. If that is the
                # case, coerce to using the double quote.
                value_with_funny_double_quote = property_default_value[0] == '`'
                if value_with_funny_double_quote:
                    property_default_value = '"{}"'.format(property_default_value[2:-2])
        
                property_names_and_defaults.append((property_name, property_default_value))
        
                i -= 1
        
            else:
                i += 1
        
            index_of_last_word_second_sentence = j + i
    
        method_names = []
        method_params = {}
        method_actions = {}
        # Step 1. Parse the method names.
        index_of_first_word_third_sentence = index_of_last_word_second_sentence + 1
        j = index_of_first_word_third_sentence
        
        # Skip two tokens (pronoun and can)
        j += 2
        
        i = 0
        
        while True:
            token = word_tokens[j+i]
            if token == '.':
                break
        
            if token not in (',', 'and'):
                method_names.append(token)
        
            i += 1
        
        # Step 2. Parse the method arguments
        # Each method has its arguments and actions defined in a single
        # sentence that must appear after the method names declaration
        # sentence.
        # From this point on, all remaining tokens will be method definition
        # tokens, and then the paragraph must end.
        method_definition_tokens = word_tokens[j+i+1:]
        method_definition_sentences = []
        
        beginning_of_sentence = 0
        end_of_sentence = method_definition_tokens.index('end', beginning_of_sentence)
        while end_of_sentence > 0:
            method_definition_sentences.append(method_definition_tokens[
                beginning_of_sentence:end_of_sentence-1])
            beginning_of_sentence = end_of_sentence + 2
            
            try:
                end_of_sentence = method_definition_tokens.index('end', beginning_of_sentence)
            except ValueError:
                break
        
        for sentence in method_definition_sentences:
            # sentence[0] must be the word "To", so we start
            # at 1 to look for the method name
            i = 1
            method_name = sentence[i]
        
            # Check if the method has a parameter
            method_has_param = 'need' in sentence[i+2]
            if method_has_param:
                param_name = sentence[i+3]
        
                method_params[method_name] = param_name
        
                i += 4
        
            actions = []
        
            j = i + 1
            while True:
                next_comma = math.inf
                try:
                    next_comma = sentence.index(',', j)
                except ValueError:
                    pass
        
                next_and = math.inf
                try:
                    next_and = sentence.index('and', j)
                except ValueError:
                    pass
        
                action_end = min(next_comma, next_and)
                if action_end == math.inf:
                    action_end = None
        
                next_action = slice(j,action_end)
        
                action_tokens = sentence[next_action]
        
                is_print_action = len(action_tokens) > 1 and action_tokens[1].find('print') == 0
                is_increase_action = len(action_tokens) > 2 and action_tokens[2].find('increase') == 0
                is_decrease_action = len(action_tokens) > 2 and action_tokens[2].find('decrease') == 0
                is_assign_action = len(action_tokens) > 2 and action_tokens[2].find('is') == 0
                is_return_action = len(action_tokens) > 1 and action_tokens[0].find('return') == 0
                is_call_action = len(action_tokens) > 1 and action_tokens[1].find('use') == 0
        
                if is_print_action:
                    actions.append(
                        ('print', action_tokens[2:])
                    )
                elif is_increase_action:
                    actions.append(
                        ('increase', [action_tokens[1]] + action_tokens[4:])
                    )
                elif is_decrease_action:
                    actions.append(
                        ('decrease', [action_tokens[1]] + action_tokens[4:])
                    )
                elif is_assign_action:
                    actions.append(
                        ('assign', [action_tokens[1]] + action_tokens[3:])
                    )
                elif is_return_action:
                    actions.append(
                        ('return', action_tokens[1:])
                    )
                elif is_call_action:
                    actions.append(
                        ('call', action_tokens[2:])
                    )
        
                if action_end is None:
                    break
        
                j = action_end + 1
        
            method_actions[method_name] = actions
        
    
        return dict(
            class_name=class_name,
            property_names_and_defaults=property_names_and_defaults,
            method_names=method_names,
            method_params=method_params,
            method_actions=method_actions
        )
    
    def produce_class_code(self, class_metadata):
        '''
        Usage:
        >>> paragraph = """
        ... A dog is a Class.
        ... He has mood = "HAPPY", energy = 100, x = 0, y = 0 .
        ... He can Bark, Run, MoveLeft, MoveRight, MoveForward, Lay and
        ... Check.
        ... To Run he used MoveForward(2), his energy decreases in 1,
        ... his mood is "PLAY" and return 0, end.
        ... To MoveForward he needs numbersSteps, his y increases in
        ... numbersSteps, his mood is "MOVING", his energy decreases by 1, end.
        ... To MoveLeft he needs numbersSteps, his x decreases in
        ... numbersSteps, his mood is "MOVING", his energy decreases by 1, end.
        ... To MoveRight he needs numbersSteps, his x increases in numbersSteps,
        ... his mood is "MOVING", his energy decreases by 1, end.
        ... To Bark he print "barf", his energy decreases in 1, his mood is
        ... "BARKING", end.
        ... To Lay he print "relax", he print "move the
        ... Booty", his energy increases in 3, end.
        ... To Check he print "mood: " + self.mood, he print "energy: " +
        ... str(self.energy), print "Position" + str(self.coordinatePosition), end.
        ... """
        >>> transpiler = Transpiler()
        >>> class_metadata = transpiler.parse_class_paragraph(paragraph)
        >>> code = transpiler.produce_class_code(class_metadata)
        >>> print(code)
        class Dog:
            mood = "happy"
            energy = 100
            x = 0
            y = 0
        <BLANKLINE>
            def bark(self):
                print(`` barf '')
                self.energy -= 1
                self.mood = '' barking ''
        <BLANKLINE>
            def run(self):
                self.moveforward ( 2 )
                self.energy -= 1
                self.mood = `` play ''
                return 0
        <BLANKLINE>
            def moveleft(self, numberssteps):
                self.x -= numberssteps
                self.mood = `` moving ''
                self.energy -= 1
        <BLANKLINE>
            def moveright(self, numberssteps):
                self.x += numberssteps
                self.mood = `` moving ''
                self.energy -= 1
        <BLANKLINE>
            def moveforward(self, numberssteps):
                self.y += numberssteps
                self.mood = `` moving ''
                self.energy -= 1
        <BLANKLINE>
            def lay(self):
                print(`` relax '')
                print(`` move the booty '')
                self.energy += 3
        <BLANKLINE>
            def check(self):
                print(`` mood : `` + self.mood)
                print(`` energy : `` + str ( self.energy ))
        <BLANKLINE>
        <BLANKLINE>
        '''
        class_code_str = ''
        # Use string.capwords to follow python class naming convetion
        class_code_str += 'class {}:'.format(
            string.capwords(class_metadata['class_name']))
        class_code_str += '\n'
    
        for name, value in class_metadata['property_names_and_defaults']:
            class_code_str += '    {name} = {value}'.format(name=name, value=value)
            class_code_str += '\n'
    
        class_code_str += '\n'
    
        for method_name in class_metadata['method_names']:
            param_name = class_metadata['method_params'].get(method_name)
            if param_name:
                class_code_str += '    def {method_name}(self, {param_name}):\n'.format(
                    method_name=method_name, param_name=param_name)
                pass
            else:
                class_code_str += '    def {method_name}(self):\n'.format(
                    method_name=method_name)
    
            for action in class_metadata['method_actions'].get(method_name, []):
                action_name, action_value = action[0], action[1]
    
                if action_name == 'print':
                    print_value = ' '.join(action_value)
                    class_code_str += '        print({})\n'.format(print_value)
                elif action_name == 'increase':
                    var = action_value[0]
                    amount = ' '.join(action_value[1:])
                    class_code_str += '        self.{var} += {amount}\n'.format(
                        var=var, amount=amount
                    )
                elif action_name == 'decrease':
                    var = action_value[0]
                    amount = ' '.join(action_value[1:])
                    class_code_str += '        self.{var} -= {amount}\n'.format(
                        var=var, amount=amount
                    )
                elif action_name == 'assign':
                    var = action_value[0]
                    value = ' '.join(action_value[1:])
                    class_code_str += '        self.{var} = {value}\n'.format(
                        var=var, value=value
                    )
                elif action_name == 'return':
                    return_value = ' '.join(action_value)
                    class_code_str += '        return {return_value}\n'.format(
                        return_value=return_value
                    )
                elif action_name == 'call':
                    class_code_str += '        self.{}\n'.format(' '.join(action_value))
    
            class_code_str += '\n'
    
        return class_code_str
    
    def tokenize_words(self, string):
        '''Returns a list of the words contained in string which is assumed
        to be a sentence.
    
        Arguments:
        string -- string represeting a sentence
        
        Usage:
        >>> transpiler = Transpiler()
        >>> transpiler.tokenize_words('a dog is a class.')
        ['a', 'dog', 'is', 'a', 'class', '.']
        '''
        return nltk.word_tokenize(string)
    
    def part_of_speech_tag(self, tokens):
        '''Returns a list of (word, tag) tuples for each word in tokens.
    
        Tags are strings that represent the role that a word takes in a text.
        For example a tag of 'NN' means the word is a noun, a tag of 'VBZ'
        means a verb, present tense, 3rd person singular. To know what a
        particular tag means you can run the following code:
    
        nltk.help.upenn_tagset('<TAG>')
    
        Arguments:
        tokens -- list of words (str)
        
        Usage:
        >>> transpiler = Transpiler()
        >>> tokens = transpiler.tokenize_words('a dog is a class')
        >>> transpiler.part_of_speech_tag(tokens)
        [('a', 'DT'), ('dog', 'NN'), ('is', 'VBZ'), ('a', 'DT'), ('class', 'NN')]
        '''
        return nltk.pos_tag(tokens)
